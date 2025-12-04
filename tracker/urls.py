from django.urls import path
from tracker.views import application_detail, upcoming_interviews


app_name = 'tracker'

urlpatterns = [
    path('applications/<int:pk>/', application_detail, name='application_detail'),
    path('interviews/upcoming/', upcoming_interviews, name='upcoming_interviews'),
]
