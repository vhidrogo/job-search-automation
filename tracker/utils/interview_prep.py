from tracker.models import (
    Application,
    Interview,
    InterviewPreparation,
    InterviewPreparationBase,
)
from tracker.services import InterviewPrepGenerator


def generate_base_prep_for_application(application_id: int) -> dict:
    """
    Generate base interview preparation for an application.
    
    Args:
        application_id: ID of application to generate base prep for.
        
    Returns:
        Dict with generation results: {"created": bool, "skipped": bool}
        
    Raises:
        Application.DoesNotExist: If application not found.
        ValueError: If application has no resume.
    """
    application = Application.objects.select_related("job__resume").get(id=application_id)
    
    if hasattr(application, "interview_prep_base"):
        return False
    
    generator = InterviewPrepGenerator()
    base_schema = generator.generate_base_preparation(application)
    
    InterviewPreparationBase.objects.create(
        application=application,
        formatted_jd=base_schema.formatted_jd,
        company_context=base_schema.company_context,
        primary_drivers=base_schema.primary_drivers,
        background_narrative=base_schema.background_narrative,
        resume_defense_prep=base_schema.resume_defense_prep,
    )
    
    return True


def generate_prep_for_interview(interview_id: int) -> dict:
    """
    Generate interview-specific preparation for an interview.
    
    Args:
        interview_id: ID of interview to generate prep for.
        
    Returns:
        Dict with generation results: {"created": bool, "skipped": bool}
        
    Raises:
        Interview.DoesNotExist: If interview not found.
        ValueError: If base prep doesn't exist or application has no resume.
    """
    interview = Interview.objects.select_related(
        "application__job__resume",
        "application__interview_prep_base"
    ).get(id=interview_id)
    
    if hasattr(interview, "preparation"):
        return False
    
    generator = InterviewPrepGenerator()
    interview_schema = generator.generate_interview_preparation(interview)
    
    InterviewPreparation.objects.create(
        interview=interview,
        prep_plan=interview_schema.prep_plan,
        predicted_questions=interview_schema.predicted_questions,
        interviewer_questions=interview_schema.interviewer_questions,
        technical_deep_dives=interview_schema.technical_deep_dives,
    )
    
    return True
