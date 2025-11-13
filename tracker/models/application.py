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
        ordering = ["-applied_date"]
        indexes = [
            models.Index(fields=["job"])
        ]

    def __str__(self):
        return f"{self.applied_date.date()} {self.job.company} - {self.job.listing_job_title}"
