from django.urls import path
from tracker.views import application_detail, company_applications, upcoming_interviews


app_name = 'tracker'

urlpatterns = [
    path('applications/<int:pk>/', application_detail, name='application_detail'),
    path('companies/<str:company_name>/', company_applications, name='company_applications'),
    path('interviews/upcoming/', upcoming_interviews, name='upcoming_interviews'),
]
