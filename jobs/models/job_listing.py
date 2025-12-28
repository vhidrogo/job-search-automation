from django.db import models

from jobs.models import Company


class JobListing(models.Model):
    """
    Represents a job posting fetched from a company's job board.
    Tracks user interaction: seen, interested, dismissed.
    Named JobListing to avoid confusion with tracker.Job (applied jobs).
    """
    
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
    
    seen = models.BooleanField(
        default=False,
        help_text="User has reviewed this job"
    )
    interested = models.BooleanField(
        default=False,
        help_text="User marked as potentially interesting"
    )
    dismissed = models.BooleanField(
        default=False,
        help_text="User dismissed as not a fit"
    )
    
    first_seen = models.DateTimeField(auto_now_add=True)
    last_fetched = models.DateTimeField(
        auto_now=True,
        help_text="Last time this job appeared in API results"
    )
    is_stale = models.BooleanField(
        default=False,
        help_text="No longer appears in API results"
    )
    
    class Meta:
        unique_together = [["company", "external_id"]]
        ordering = ["-first_seen"]
        indexes = [
            models.Index(fields=["seen", "is_stale", "dismissed"]),
            models.Index(fields=["company", "external_id"]),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company.name}"
