from django.contrib import admin
from .models import Position, Employee, Task, Timesheet, TimesheetHistory


class TimesheetAdmin(admin.ModelAdmin):
    list_display = ('employee', 'task', 'start_time', 'end_time')
    search_fields = ('employee', 'task')


admin.site.register(Position)
admin.site.register(Employee)
admin.site.register(Task)
admin.site.register(TimesheetHistory)
admin.site.register(Timesheet, TimesheetAdmin)
