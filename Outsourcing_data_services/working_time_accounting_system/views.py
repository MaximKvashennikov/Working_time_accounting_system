from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.views import View
from .importers import PositionImporter, EmployeeImporter, TimesheetImporter
from .forms import ImportForm, EmployeeTimesheetsForm, DeleteTimesheetForm
from django.db import transaction, connection
from django.db.models import Sum, F, ExpressionWrapper, IntegerField, FloatField, Q
from .models import Timesheet
from django.db.models.functions import Cast, Round, Extract
from django.views.generic import TemplateView, ListView, FormView
from django.db.models.signals import pre_delete


class TimesheetListView(ListView):
    template_name = 'index.html'
    context_object_name = 'timesheets'

    def get_queryset(self):
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM working_time_accounting_system_timesheet WHERE employee_id = {self.kwargs['employee_id']}")
            results = cursor.fetchall()
            return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["employee_timesheets_form"] = EmployeeTimesheetsForm()
        context["delete_timesheet_form"] = DeleteTimesheetForm()
        return context


class DeleteTimesheetFormView(FormView):
    template_name = 'index.html'
    form_class = DeleteTimesheetForm
    success_url = reverse_lazy('timesheet_management')

    @transaction.atomic
    def form_valid(self, form):
        timesheet_id = form.cleaned_data.get('timesheet_id')
        try:
            timesheet = Timesheet.objects.get(id=timesheet_id)
        except Timesheet.DoesNotExist:
            messages.error(self.request, f'Timesheet with ID {timesheet_id} does not exist')
            return redirect('timesheet_management')

        employee_name = timesheet.employee.employee_name
        pre_delete.send(sender=Timesheet, instance=timesheet)
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM working_time_accounting_system_timesheet WHERE id = {timesheet_id}")
            messages.success(self.request, f'Timesheet with ID {timesheet_id} for {employee_name} has been deleted')
        return super().form_valid(form)


class EmployeeTimesheetsFormView(FormView):
    form_class = EmployeeTimesheetsForm
    template_name = "index.html"
    success_url = reverse_lazy('timesheet_list')

    def form_valid(self, form):
        employee = form.cleaned_data.get('employee')
        self.success_url = reverse_lazy('timesheet_list', args=[employee.id])
        return super().form_valid(form)


class TimesheetManagementView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["employee_timesheets_form"] = EmployeeTimesheetsForm()
        context["delete_timesheet_form"] = DeleteTimesheetForm()
        return context


class ImportDataFormView(FormView):
    template_name = 'import.html'
    form_class = ImportForm
    success_url = reverse_lazy('import_result')

    def form_valid(self, form):
        positions = form.cleaned_data['positions_file']
        employees = form.cleaned_data['employees_file']
        timesheets = form.cleaned_data['timesheets_file']

        position_errors, position_count = PositionImporter.import_from_csv(positions)
        employee_errors, employee_count = EmployeeImporter.import_from_csv(employees)
        timesheet_errors, timesheet_count = TimesheetImporter.import_from_csv(timesheets)

        for error in position_errors:
            messages.error(self.request, error)
        for error in employee_errors:
            messages.error(self.request, error)
        for error in timesheet_errors:
            messages.error(self.request, error)

        self.request.session['import_results'] = {
            'position_count': position_count,
            'employee_count': employee_count,
            'timesheet_count': timesheet_count,
        }
        return super().form_valid(form)


class ImportResultView(TemplateView):
    template_name = 'import_result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import_results = self.request.session.get('import_results', None)
        if import_results:
            context.update(import_results)
        return context


class ReportView(TemplateView):
    template_name = 'report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['top5_long_tasks'] = self.top5_long_tasks()
        context['top5_cost_tasks'] = self.top5_cost_tasks()
        context['top5_employees'] = self.top5_employees()
        return context

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
