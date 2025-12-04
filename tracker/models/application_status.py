from django.db import models
from django.utils import timezone


class ApplicationStatus(models.Model):
    class State(models.TextChoices):
        CALLBACK = "callback", "Callback"
        CLOSED = "closed", "Closed"
        REJECTED = "rejected", "Rejected"

    application = models.OneToOneField(
        "Application",
        on_delete=models.CASCADE,
        related_name="status",
    )
    state = models.CharField(max_length=16, choices=State.choices)
    status_date = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Application Statuses"
