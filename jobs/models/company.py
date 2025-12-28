from django.db import models

from jobs.clients import WorkdayClient, WorkdayCompanyConfig


class Company(models.Model):
    """
    Represents a company with a job board.
    Platform-specific config stored in related models (WorkdayConfig, etc.)
    """
    
    class Platform(models.TextChoices):
        WORKDAY = "workday", "Workday"
        GREENHOUSE = "greenhouse", "Greenhouse"
        LEVER = "lever", "Lever"
        ASHBY = "ashby", "Ashby"
    
    name = models.CharField(max_length=200, unique=True, db_index=True)
    platform = models.CharField(max_length=50, choices=Platform.choices)
    active = models.BooleanField(
        default=True,
        help_text="Whether to include this company in job syncing"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ["name"]
    
    def __str__(self):
        return f"{self.name} ({self.get_platform_display()})"
    
    def get_job_fetcher(self):
        """Factory method to get appropriate client for this company's platform"""
        if self.platform == self.Platform.WORKDAY:
            config = WorkdayCompanyConfig.from_django_model(self.workday_config)
            return WorkdayClient(config)
        else:
            raise NotImplementedError(f"Platform {self.platform} not yet supported")
