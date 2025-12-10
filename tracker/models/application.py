from django.db import models
from django.utils import timezone


class Application(models.Model):
    job = models.OneToOneField(
        "Job",
        on_delete=models.CASCADE,
        related_name="application",
    )
    applied_date = models.DateTimeField(default=timezone.now)
    desired_salary_min = models.PositiveIntegerField(null=True, blank=True)

    def clean(self):
        super().clean()
        if self.desired_salary_min and self.desired_salary_min < 1000:
            self.desired_salary_min *= 1000

    class Meta:
        ordering = ["-applied_date"]
        indexes = [
            models.Index(fields=["job"])
        ]

    def __str__(self):
        external_job_id = f" ({self.job.external_job_id})" if self.job.external_job_id else ""
        return (
            f"{timezone.localdate(self.applied_date)} {self.job.company}"
            f" - {self.job.listing_job_title}{external_job_id}"
        )
