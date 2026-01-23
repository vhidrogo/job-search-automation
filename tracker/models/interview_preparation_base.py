from django.db import models


class InterviewPreparationBase(models.Model):
    """
    Base preparation data generated once per application.
    Contains job-agnostic analysis and narrative.

    Fields:
        - application: FK to the associated appliation.
        - formatted_jd: Formatted job description with bolded key phrases.
        - company_context: Company & product context (markdown with headers).
        - primary_drivers: Primary callback drivers (markdown list with bold titles).
        - background_narrative: Targeted background narrative (markdown with 3 subsections)
        - resume_defense_prep: Resume bullet defense strategies (markdown).
    """
    application = models.OneToOneField(
        "Application",
        on_delete=models.CASCADE,
        related_name="interview_prep_base"
    )
    
    formatted_jd = models.TextField(
        help_text="Markdown-formatted job description with bolded callback drivers"
    )
    
    company_context = models.TextField(
        help_text="What company does, products, mission, why team exists"
    )
    
    primary_drivers = models.TextField(
        help_text="1-3 key reasons resume passed screening, with justifications"
    )
    
    background_narrative = models.TextField(
        help_text="Opening line, core narrative, forward hook (markdown formatted)"
    )

    resume_defense_prep = models.TextField(
        help_text="Resume bullet defense strategies (markdown)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
