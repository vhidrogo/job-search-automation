from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from tracker.models import Application


def application_detail(request, pk):
    """
    Display comprehensive application details including:
    - Job information
    - Application timeline
    - Resume (HTML-rendered with styling)
    - Past interviews with notes
    - Upcoming interviews
    """
    application = get_object_or_404(
        Application.objects.select_related(
            "job",
            "job__resume",
            "job__resume__template"
        ).prefetch_related(
            "interviews"
        ),
        pk=pk
    )
    
    now = timezone.now()
    
    all_interviews = application.interviews.all().order_by("scheduled_at")
    past_interviews = [i for i in all_interviews if i.scheduled_at <= now]
    upcoming_interviews = [i for i in all_interviews if i.scheduled_at > now]
    
    resume_html = None
    resume_css = None
    resume_exists = hasattr(application.job, "resume")
    
    if resume_exists:
        resume = application.job.resume
        resume_html = resume.render_to_html()
        resume_css = resume.get_css_content()
    
    context = {
        "application": application,
        "job": application.job,
        "resume_html": resume_html,
        "resume_css": resume_css,
        "resume_exists": resume_exists,
        "past_interviews": past_interviews,
        "upcoming_interviews": upcoming_interviews,
        "current_time": now,
        "requirements": (
            application.job.requirements.all() 
            if hasattr(application, "status") and application.status.state == "rejected" else None
        ),
    }
    
    return render(request, "application_detail.html", context)
