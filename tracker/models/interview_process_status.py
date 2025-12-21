from django.db import models


class InterviewProcessStatus(models.Model):
    """
    Represents the final outcome of the entire interview process for an application.
    This is an event-driven record created only when a final outcome is determined
    (offer, rejection, ghosting, or withdrawal). Most applications won"t have this
    record until the interview process concludes.
    
    Unlike individual Interview records which track each stage, this captures the
    overall result of the interview pipeline regardless of how many rounds occurred.
    """
    
    class Outcome(models.TextChoices):
        OFFER = "offer", "Offer"
        REJECTED = "rejected", "Rejected"
        FAILED = "failed", "Failed"
        GHOSTED = "ghosted", "Ghosted"
        WITHDREW = "withdrew", "Withdrew"
    
    application = models.OneToOneField(
        "Application",
        on_delete=models.CASCADE,
        related_name="interview_process_status"
    )
    
    outcome = models.CharField(max_length=50, choices=Outcome.choices)
    
    outcome_date = models.DateField(
        help_text="Date when the outcome was determined or notification was received"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Optional context about the outcome (e.g., feedback received, reason for withdrawal)"
    )
    
    class Meta:
        verbose_name = "Interview Process Status"
        verbose_name_plural = "Interview Process Statuses"
    
    def __str__(self):
        return f"{self.application} - {self.get_outcome_display()}"
    