from django.db import models

from jobs.models import Company


class WorkdayConfig(models.Model):
    """Workday-specific configuration for a company"""
    
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name="workday_config",
        limit_choices_to={"platform": Company.Platform.WORKDAY}
    )
    
    base_url = models.URLField(help_text="e.g., https://company.wd5.myworkdayjobs.com")
    tenant = models.CharField(max_length=100, help_text="e.g., company_name")
    site = models.CharField(max_length=100, help_text="e.g., company_careers")
    location_filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON mapping location names to IDs: {\"Seattle\": \"abc123...\"}"
    )
    
    def __str__(self):
        return f"Workday config for {self.company.name}"
