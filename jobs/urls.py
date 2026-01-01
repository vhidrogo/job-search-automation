from django.urls import path
from jobs.views import bulk_dismiss, bulk_mark_applied, job_listings_view, update_job_status

app_name = "jobs"

urlpatterns = [
    path("", job_listings_view, name="job_listings"),
    path('<int:job_id>/update-status/', update_job_status, name='update_job_status'),
	path('bulk-dismiss/', bulk_dismiss, name='bulk_dismiss'),
    path('bulk-mark-applied/', bulk_mark_applied, name='bulk_mark_applied'),
]
