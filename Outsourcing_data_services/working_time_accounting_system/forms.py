from django import forms
from .models import Position, Employee, Timesheet


class EmployeeTimesheetsForm(forms.Form):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all())


class DeleteTimesheetForm(forms.Form):
    timesheet_id = forms.IntegerField()


def validate_filename(filename, expected):
    if not filename.name.lower() == expected:
        raise forms.ValidationError(f"Incorrect file name: '{filename}'. Expected: '{expected}'")


class ImportForm(forms.ModelForm):
    positions_file = forms.FileField(
        validators=[lambda f: validate_filename(f, 'positions.csv')],
        widget=forms.FileInput(attrs={
            'class': 'inline-flex items-center justify-center',
            'placeholder': 'Import Positions',
        })
    )

    employees_file = forms.FileField(
        validators=[lambda f: validate_filename(f, 'employees.csv')],
        widget=forms.FileInput(attrs={
            'class': 'inline-flex items-center justify-center',
            'placeholder': 'Import Employees',
        })
    )

    timesheets_file = forms.FileField(
        validators=[lambda f: validate_filename(f, 'timesheet.csv')],
        widget=forms.FileInput(attrs={
            'class': 'inline-flex items-center justify-center',
            'placeholder': 'Import Timesheets',
        })
    )

    class Meta:
        model = Timesheet
        fields = ["positions_file", "employees_file", "timesheets_file"]
