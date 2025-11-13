from django.db import models
from django.utils import timezone

from .choices import ApplicationState


class ApplicationStatus(models.Model):
    application = models.OneToOneField(
        "Application",
        on_delete=models.CASCADE,
        related_name="status",
    )
    state = models.CharField(max_length=16, choices=ApplicationState.choices)
    status_date = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Application Statuses"
