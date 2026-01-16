from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from tracker.models import Application, Interview


def interview_preparation_view(request, application_id):
    """
    Display interview preparation for an application.
    
    Shows base preparation (always) and interview-specific preparation
    filtered by selected interview (default to first scheduled interview).
    """
    application = get_object_or_404(
        Application.objects.select_related(
            "job",
            "interview_prep_base"
        ).prefetch_related("interviews"),
        id=application_id
    )
    
    if not hasattr(application, "interview_prep_base"):
        raise Http404("Interview preparation not found for this application")
    
    prep_base = application.interview_prep_base
    
    interviews = application.interviews.order_by("scheduled_at")

    selected_interview = None
    interview_prep = None
    
    if interviews.exists():
        selected_interview_id = request.GET.get("interview_id")
        if selected_interview_id:
            selected_interview = get_object_or_404(
                Interview.objects.select_related("preparation"),
                id=selected_interview_id,
                application=application
            )
        else:
            now = timezone.now()
            selected_interview = (
                interviews.filter(scheduled_at__gte=now).order_by("scheduled_at").first()
                or interviews.filter(scheduled_at__lt=now).order_by("-scheduled_at").first()
            )
        
        if hasattr(selected_interview, "preparation"):
            interview_prep = selected_interview.preparation
    
    context = {
        "application": application,
        "job": application.job,
        "prep_base": prep_base,
        "interviews": interviews,
        "selected_interview": selected_interview,
        "interview_prep": interview_prep,
    }
    
    return render(request, "interview_preparation.html", context)
