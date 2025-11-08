from django.db import models


class ExperienceRole(models.Model):
    """
    Represents a past work role used to generate experience bullets for resumes.

    Fields:
      - key: Stable identifier used by templates to reference this role.
      - company: Employer name.
      - title: Job title.
      - start_date: The date the role began.
      - end_date: The date the role ended.
      - location: Location where the role was set in.
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
    start_date = models.DateField(
        help_text="The date the role began.",
    )
    end_date = models.DateField(
        help_text="The date the role ended.",
    )
    location = models.CharField(
        max_length=50,
        help_text="Location where the role was set in. (e.g 'Seattle, WA', 'Remote')",
    )
    

    class Meta:
        app_label = "resume"

    def __str__(self) -> str:
        return f"{self.title} - {self.company}"
