from django.db import models
from django.utils import timezone


class Application(models.Model):
    job = models.OneToOneField(
        "Job",
        on_delete=models.CASCADE,
        related_name="application",
    )
    applied_date = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["job"])
        ]
