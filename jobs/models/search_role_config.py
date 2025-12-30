from django.db import models

from jobs.models import SearchRole


class SearchRoleConfig(models.Model):
    role = models.CharField(
        max_length=100,
        choices=SearchRole.choices,
        unique=True,
        help_text="Role to configure search behavior for"
    )
    exclude_terms = models.JSONField(
        default=list,
        help_text="Terms to exclude from job titles for this role"
    )
    
    class Meta:
        verbose_name = "Search Role Configuration"
        verbose_name_plural = "Search Role Configurations"
    
    def __str__(self):
        return f"{self.get_role_display()}"
