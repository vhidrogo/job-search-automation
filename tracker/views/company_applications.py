from django.shortcuts import render
from django.db.models import Q
from tracker.models import Application


def company_applications(request, company_name):
    """
    Display all applications for a specific company with filterable status.
    Used as operational reference when browsing a company"s careers page.
    
    Status categories:
    - Active: No response yet OR interviewing (callback without final outcome)
    - Inactive: Rejected, closed, or interview process concluded
    """
    status_filter = request.GET.get("filter", "all")
    
    applications = Application.objects.filter(
        job__company=company_name
    ).select_related(
        "job",
        "status",
        "interview_process_status"
    ).order_by("-applied_date")
    
    if status_filter == "active":
        # Active: no status OR (callback without interview process conclusion)
        applications = applications.filter(
            Q(status__isnull=True) | 
            Q(status__state="callback", interview_process_status__isnull=True)
        )
    elif status_filter == "inactive":
        # Inactive: rejected, closed, OR interview process concluded
        applications = applications.filter(
            Q(status__state__in=["rejected", "closed"]) |
            Q(interview_process_status__isnull=False)
        )
    
    applications_with_status = []
    for app in applications:
        display_status = _get_display_status(app)
        applications_with_status.append({
            "application": app,
            "display_status": display_status,
        })
    
    context = {
        "company_name": company_name,
        "applications": applications_with_status,
        "status_filter": status_filter,
        "total_count": len(applications_with_status),
    }
    
    return render(request, "company_applications.html", context)


def _get_display_status(application):
    """
    Derive human-readable status for display.
    
    Priority:
    1. Interview process outcome (if exists)
    2. Callback → "Interviewing"
    3. Other ApplicationStatus states
    4. No status → "No Response"
    """
    if hasattr(application, "interview_process_status"):
        return application.interview_process_status.get_outcome_display()
    
    if hasattr(application, "status"):
        state = application.status.state
        if state == "callback":
            return "Interviewing"
        return application.status.get_state_display()
    
    return "No Response"
