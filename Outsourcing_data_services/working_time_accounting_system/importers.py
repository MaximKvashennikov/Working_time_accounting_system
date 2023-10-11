import csv
from datetime import datetime
from django.db import transaction
from .models import Position, Employee, Task, Timesheet
from django.core.exceptions import ValidationError
from django.db import IntegrityError


class PositionImporter:
    @staticmethod
    def import_from_csv(uploaded_file):
        csvfile = uploaded_file.read().decode('utf-8').splitlines()
        reader = csv.reader(csvfile)
        errors = []
        with transaction.atomic():
            position_count = 0
            for row in reader:
                position_name, hourly_rate = row
                hourly_rate = int(hourly_rate)
                try:
                    position, created = Position.objects.get_or_create(
                        position_name=position_name,
                        hourly_rate=hourly_rate,
                    )
                    if not created:
                        print(
                            f"Skipping position '{position_name}', as it already exists in the database.")
                    if created:
                        position_count += 1
                except (IntegrityError, ValidationError) as e:
                    errors.append(f"Error adding position '{position_name}': {str(e)}")

        return errors, position_count


class EmployeeImporter:
    @staticmethod
    def import_from_csv(uploaded_file):
        csvfile = uploaded_file.read().decode('utf-8').splitlines()
        reader = csv.reader(csvfile)
        errors = []
        with transaction.atomic():
            employee_count = 0
            for row in reader:
                employee_name, position_name = row
                position = Position.objects.get(position_name=position_name)
                try:
                    employee, created = Employee.objects.get_or_create(
                        employee_name=employee_name,
                        position=position,
                    )
                    if not created:
                        print(
                            f"Skipping employee '{employee_name}', as it already exists in the database.")
                    if created:
                        employee_count += 1
                except (IntegrityError, ValidationError) as e:
                    errors.append(f"Error adding employee '{employee_name}': {str(e)}")

        return errors, employee_count


class TimesheetImporter:
    @staticmethod
    def import_from_csv(uploaded_file):
        csvfile = uploaded_file.read().decode('utf-8').splitlines()
        rows = list(csv.reader(csvfile))
        datetime_format = "%Y-%m-%d %H:%M:%S"
        errors = []
        with transaction.atomic():
            for row in rows:
                task_name, _, _, _ = row
                try:
                    task, created = Task.objects.get_or_create(task_name=task_name)
                    if not created:
                        print(
                            f"Skipping task '{task_name}', as it already exists in the database.")
                except (IntegrityError, ValidationError) as e:
                    errors.append(f"Error adding task '{task_name}': {str(e)}")

        with transaction.atomic():
            timesheet_count = 0
            for row in rows:
                task_name, employee_name, start_time, end_time = row
                task = Task.objects.get(task_name=task_name)
                employee = Employee.objects.get(employee_name=employee_name)
                start_time = datetime.strptime(start_time, datetime_format)
                end_time = datetime.strptime(end_time, datetime_format)
                try:
                    timesheet, created = Timesheet.objects.get_or_create(
                        employee=employee,
                        task=task,
                        start_time=start_time,
                        end_time=end_time,
                    )
                    if not created:
                        print(f"Skipping timesheet '{employee}: {task}', as it already exists in the database.")
                    if created:
                        timesheet_count += 1
                except (IntegrityError, ValidationError) as e:
                    errors.append(f"Error adding timesheet entry: {str(e)}")

        return errors, timesheet_count
