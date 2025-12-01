from django.urls import path
from tracker.views import upcoming_interviews


app_name = 'tracker'

urlpatterns = [
    path('interviews/upcoming/', upcoming_interviews, name='upcoming_interviews'),
]
