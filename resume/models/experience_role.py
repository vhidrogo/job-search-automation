from django.db import models


class ExperienceRole(models.Model):
    """
    Represents a past work role used to generate experience bullets for resumes.

    Fields:
      - key: Stable identifier used by templates to reference this role.
      - company: Employer name.
      - title: Job title.
      - display_name: Optional human-facing name; if null, renders as "title – company".
    """

    key = models.CharField(
        max_length=50,
        unique=True,
        help_text="Stable identifier used by templates (e.g., 'navit', 'amazon_sde').",
    )
    company = models.CharField(
        max_length=255,
        help_text="Employer name (e.g., 'Nav.it').",
    )
    title = models.CharField(
        max_length=255,
        help_text="Job title (e.g., 'Software Engineer').",
    )
    display_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Optional human-facing name; if empty, renders as 'title – company'.",
    )

    class Meta:
        app_label = "resume"

    def __str__(self) -> str:
        if self.display_name:
            return self.display_name
        return f"{self.title} – {self.company}"
