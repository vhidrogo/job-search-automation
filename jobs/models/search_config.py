from django.db import models


class SearchConfig(models.Model):
    search_term = models.CharField(
        max_length=200,
        unique=True,
        help_text="Primary search keyword (e.g., 'Software Engineer', 'Data Analyst')"
    )
    exclude_terms = models.JSONField(
        default=list,
        help_text="Terms to exclude from job titles"
    )
    active = models.BooleanField(
        default=True,
        help_text="Include in automated syncs"
    )
    
    class Meta:
        verbose_name = "Search Configuration"
        verbose_name_plural = "Search Configurations"
    
    def __str__(self):
        return self.search_term
