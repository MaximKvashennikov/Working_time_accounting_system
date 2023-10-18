from django.urls import path
from . import views


urlpatterns = [
    path('', views.TimesheetManagementView.as_view(), name='timesheet_management'),
    path('import/', views.ImportDataFormView.as_view(), name='import_data'),
    path('import_result/', views.ImportResultView.as_view(), name='import_result'),
    path('report/', views.ReportView.as_view(), name='report'),
    path('submit/', views.EmployeeTimesheetsFormView.as_view(), name='employee_timesheets_submit'),
    path('timesheet_list/<int:employee_id>/', views.TimesheetListView.as_view(), name='timesheet_list'),
    path('delete_timesheet/', views.DeleteTimesheetFormView.as_view(), name='delete_timesheet'),
]
