from django.db import models


class Interview(models.Model):
    """
    Represents a single interview in the hiring process.
    
    An application can have multiple interviews across different stages.
    Each interview has a stage (recruiter/technical/final), optional format
    (phone/virtual), and optional focus area (coding/system design/etc).
    """
    
    class Stage(models.TextChoices):
        RECRUITER_SCREEN = 'recruiter_screen', 'Recruiter Screen'
        HIRING_MANAGER_SCREEN = 'hiring_manager_screen', 'Hiring Manager Screen'
        TECHNICAL_SCREEN = 'technical_screen', 'Technical Screen'
        FINAL_LOOP = 'final_loop', 'Final Loop'
    
    class Format(models.TextChoices):
        PHONE_CALL = 'phone_call', 'Phone Call'
        VIRTUAL_MEETING = 'virtual_meeting', 'Virtual Meeting'
    
    class Focus(models.TextChoices):
        CODING = 'coding', 'Coding'
        SYSTEM_DESIGN = 'system_design', 'System Design'
        BEHAVIORAL = 'behavioral', 'Behavioral'
        HIRING_MANAGER = 'hiring_manager', 'Hiring Manager'
    
    application = models.ForeignKey(
        "Application",
        on_delete=models.CASCADE,
        related_name="interviews"
    )
    stage = models.CharField(max_length=50, choices=Stage.choices)
    format = models.CharField(max_length=50, choices=Format.choices, blank=True)
    focus = models.CharField(max_length=50, choices=Focus.choices, blank=True)
    interviewer_name = models.CharField(max_length=200, blank=True)
    interviewer_title = models.CharField(max_length=200, blank=True)
    scheduled_at = models.DateTimeField()
    notes = models.TextField(blank=True, help_text="Freeform interview notes")
    