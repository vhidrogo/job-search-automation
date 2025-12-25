from django.urls import path
from tracker.views import (
    application_detail,
    application_metrics,
    company_applications,
    interview_preparation_view,
    upcoming_interviews,
)


app_name = "tracker"

urlpatterns = [
    path("applications/<int:pk>/", application_detail, name="application_detail"),
    path('applications/<int:application_id>/interview-prep/', interview_preparation_view, name='interview_preparation'),
    path("companies/<str:company_name>/", company_applications, name="company_applications"),
    path("interviews/upcoming/", upcoming_interviews, name="upcoming_interviews"),
    path("metrics/", application_metrics, name="application_metrics"),
]
