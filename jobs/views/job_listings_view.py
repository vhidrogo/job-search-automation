from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from jobs.models import Company, JobListing
from tracker.models import Job


def job_listings_view(request):
    """
    Main view for displaying available job listings.
    Shows only new jobs by default, excluding interested, dismissed and applied jobs.
    """
    status_filter = request.GET.get("status", JobListing.Status.NEW)
    company_filter = request.GET.get("company")
    keywords_filter = request.GET.get("keywords")
    
    applied_ids = set(Job.objects.values_list("external_job_id", flat=True))
    
    jobs = JobListing.objects.filter(
        company__active=True,
        is_stale=False
    ).exclude(
        external_id__in=applied_ids
    ).select_related("company")

    if status_filter:
        jobs = jobs.filter(status=status_filter)
    
    if company_filter:
        jobs = jobs.filter(company__name__iexact=company_filter)
    
    if keywords_filter:
        jobs = jobs.filter(
            Q(title__icontains=keywords_filter) | Q(location__icontains=keywords_filter)
        )
    
    companies = Company.objects.filter(active=True).order_by("name")
    
    total_unseen = JobListing.objects.filter(
        company__active=True,
        is_stale=False,
        status=JobListing.Status.NEW
    ).exclude(external_id__in=applied_ids).count()
    
    context = {
        "jobs": jobs.order_by("-last_fetched"),
        "companies": companies,
        "total_unseen": total_unseen,
        "filters": {
            "company": company_filter,
            "keywords": keywords_filter,
            "status": status_filter,
        }
    }
    
    return render(request, "job_listings.html", context)


@require_POST
def update_job_status(request, job_id):
    """AJAX endpoint to update job status"""
    job = get_object_or_404(JobListing, id=job_id)
    new_status = request.POST.get('status')
    
    if new_status in [s.value for s in JobListing.Status]:
        job.status = new_status
        job.save()
        return JsonResponse({"status": "success"})
    
    return JsonResponse({"status": "error", "message": "Invalid status"}, status=400)


@require_POST
def bulk_dismiss_new(request):
    """AJAX endpoint to mark all NEW jobs as dismissed"""
    applied_ids = set(Job.objects.values_list("external_job_id", flat=True))
    
    count = JobListing.objects.filter(
        company__active=True,
        is_stale=False,
        status=JobListing.Status.NEW
    ).exclude(external_id__in=applied_ids).update(status=JobListing.Status.DISMISSED)
    
    return JsonResponse({"status": "success", "count": count})

@require_POST
def bulk_mark_applied(request):
    """AJAX endpoint to mark all INTERESTED jobs as applied"""
    applied_ids = set(Job.objects.values_list("external_job_id", flat=True))
    
    count = JobListing.objects.filter(
        company__active=True,
        is_stale=False,
        status=JobListing.Status.INTERESTED
    ).exclude(external_id__in=applied_ids).update(status=JobListing.Status.APPLIED)
    
    return JsonResponse({"status": "success", "count": count})
