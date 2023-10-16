from django.shortcuts import render
from django.contrib import messages
from django.views import View
from .importers import PositionImporter, EmployeeImporter, TimesheetImporter
from .forms import ImportForm, EmployeeTimesheetsForm, DeleteTimesheetForm
from django.db import transaction, connection
from django.db.models import Count, Sum, F, DurationField, ExpressionWrapper, IntegerField, FloatField, Q
from .models import Timesheet
from django.db.models.functions import Cast, Round, Extract
from django.views.generic import TemplateView
from django.db.models.signals import pre_delete


# def get_timesheets_by_employee(employee_id):
#     return Timesheet.objects.filter(employee__id=employee_id)
#
#
# @transaction.atomic
# def delete_timesheet_by_id(timesheet_id):
#     try:
#         timesheet = Timesheet.objects.get(id=timesheet_id)
#         employee_name = timesheet.employee.employee_name
#         timesheet.delete()
#         return employee_name
#     except Timesheet.DoesNotExist:
#         return None


def get_timesheets_by_employee(employee_id):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM working_time_accounting_system_timesheet WHERE employee_id = {employee_id}")
        results = cursor.fetchall()
        return results


@transaction.atomic
def delete_timesheet_by_id(timesheet_id):
    try:
        timesheet = Timesheet.objects.get(id=timesheet_id)
    except Timesheet.DoesNotExist:
        return None
    employee_name = timesheet.employee.employee_name
    pre_delete.send(sender=Timesheet, instance=timesheet)
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM working_time_accounting_system_timesheet WHERE id = {timesheet_id}")
        return employee_name


class HomePageView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["employee_timesheets_form"] = EmployeeTimesheetsForm()
        context["delete_timesheet_form"] = DeleteTimesheetForm()
        if self.extra_context is not None and 'timesheets' in self.extra_context:
            context["timesheets"] = self.extra_context['timesheets']
        return context

    def post(self, request, *args, **kwargs):
        delete_form = DeleteTimesheetForm(request.POST)
        if delete_form.is_valid():
            timesheet_id = delete_form.cleaned_data.get('timesheet_id')
            employee_name = delete_timesheet_by_id(timesheet_id)
            if employee_name is None:
                messages.error(request, f'Timesheet with ID {timesheet_id} does not exist')
            else:
                messages.success(request, f'Timesheet with ID {timesheet_id} for {employee_name} has been deleted')
        else:
            form = EmployeeTimesheetsForm(request.POST)
            if form.is_valid():
                employee = form.cleaned_data.get('employee')
                timesheets = get_timesheets_by_employee(employee.id)
                self.extra_context = {'timesheets': timesheets}
        return self.get(request, *args, **kwargs)


class ImportDataView(View):
    def get(self, request):
        form = ImportForm()
        return render(request, 'import.html', {'form': form})

    def post(self, request):
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            positions = form.cleaned_data['positions_file']
            employees = form.cleaned_data['employees_file']
            timesheets = form.cleaned_data['timesheets_file']

            position_errors, position_count = PositionImporter.import_from_csv(positions)
            employee_errors, employee_count = EmployeeImporter.import_from_csv(employees)
            timesheet_errors, timesheet_count = TimesheetImporter.import_from_csv(timesheets)

            for error in position_errors:
                messages.error(request, error)
            for error in employee_errors:
                messages.error(request, error)
            for error in timesheet_errors:
                messages.error(request, error)

            return render(request, 'import_result.html', {
                'position_count': position_count,
                'employee_count': employee_count,
                'timesheet_count': timesheet_count,
            })
        else:
            return render(request, 'import.html', {'form': form})


class ReportView(View):
    def top5_long_tasks(self):
        long_tasks = (
            Timesheet.objects.annotate(
                spent_hours=ExpressionWrapper(
                    Cast(Extract(F("end_time") - F("start_time"), 'epoch'), output_field=IntegerField()) / 3600,
                    output_field=IntegerField()
                )
            ).values("task__task_name").annotate(
                total_hours=Sum("spent_hours")
            ).order_by("-total_hours")[:5]
        )
        return long_tasks

    def top5_cost_tasks(self):
        cost_tasks = (
            Timesheet.objects.annotate(
                spent_hours=ExpressionWrapper(
                    Cast(Extract(F("end_time") - F("start_time"), 'epoch'), output_field=IntegerField()) / 3600,
                    output_field=FloatField()
                )
            ).annotate(
                total_cost=ExpressionWrapper(
                    F("spent_hours") * F("employee__position__hourly_rate"),
                    output_field=IntegerField()
                )
            ).values("task__task_name").annotate(
                total_cost_sum=Sum("total_cost")
            ).order_by("-total_cost_sum")[:5]
        )
        return cost_tasks

    def top5_employees(self):
        employees = (
            Timesheet.objects.values("employee__employee_name").annotate(
                total_hours=Round(
                    Sum(Cast(Extract(F("end_time") - F("start_time"), 'epoch'), output_field=IntegerField())) / 3600,
                    output_field=IntegerField()
                )
            ).order_by("-total_hours")[:5]
        )
        return employees

    def get(self, request):
        context = {
            "top5_long_tasks": self.top5_long_tasks(),
            "top5_cost_tasks": self.top5_cost_tasks(),
            "top5_employees": self.top5_employees(),
        }
        return render(request, "report.html", context)
