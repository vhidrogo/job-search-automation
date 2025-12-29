from django.db import models
from django.utils import timezone

from jobs.models import Company


class JobListing(models.Model):
    """
    Represents a job posting fetched from a company's job board.
    """

    class Status(models.TextChoices):
        NEW = 'new', 'New'
        INTERESTED = 'interested', 'Interested'
        DISMISSED = 'dismissed', 'Dismissed'
        APPLIED = 'applied', 'Applied'
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="job_listings"
    )
    external_id = models.CharField(
        max_length=200,
        help_text="Job ID from the platform"
    )
    
    title = models.CharField(max_length=500)
    location = models.CharField(max_length=200, blank=True)
    url = models.URLField(max_length=1000)
    posted_on = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        help_text="Current review status of this job listing"
    )
    
    last_fetched = models.DateTimeField(
        default=timezone.now,
        help_text="Last time this job appeared in API results"
    )
    is_stale = models.BooleanField(
        default=False,
        help_text="No longer appears in API results"
    )
    
    class Meta:
        unique_together = [["company", "external_id"]]
        ordering = ["-last_fetched"]
        indexes = [
            models.Index(fields=["status", "is_stale"]),
            models.Index(fields=["company", "external_id"]),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company.name}"
