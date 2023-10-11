from django.urls import path
from . import views


urlpatterns = [
    path('', views.HomePageView.as_view(), name='timesheet'),
    path('import/', views.ImportDataView.as_view(), name='import_data'),
    path('report/', views.ReportView.as_view(), name='report'),
]
