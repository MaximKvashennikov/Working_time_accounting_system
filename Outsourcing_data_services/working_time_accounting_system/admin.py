from django.contrib import admin
from .models import Position, Employee, Task, Timesheet, TimesheetHistory


class TimesheetAdmin(admin.ModelAdmin):
    list_display = ('employee', 'task', 'start_time', 'end_time')
    search_fields = ('employee', 'task')


class TimesheetHistoryAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'task_title', 'start_time', 'end_time')
    search_fields = ('employee_id', 'task_title', 'start_time', 'end_time')


admin.site.register(Position)
admin.site.register(Employee)
admin.site.register(Task)
admin.site.register(TimesheetHistory, TimesheetHistoryAdmin)
admin.site.register(Timesheet, TimesheetAdmin)
