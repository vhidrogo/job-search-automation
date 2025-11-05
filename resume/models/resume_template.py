from django.db import models

from tracker.models.job import JobLevel, JobRole


class TemplatePath(models.TextChoices):
    """
    Enum of available HTML resume templates.

    Paths are relative to the template directory (not absolute file system paths).
    """
    SOFTWARE_ENGINEER_I = "html/software_engineer_i.html", "Software Engineer I"
    SOFTWARE_ENGINEER_II = "html/software_engineer_ii.html", "Software Engineer II"


class StylePath(models.TextChoices):
    """
    Enum of available CSS stylesheet options for resume templates.

    Paths are relative to the static directory (not absolute file system paths).
    """
    COMPACT = "css/resume_compact.css", "Compact"
    STANDARD = "css/resume_standard.css", "Standard"


class ResumeTemplate(models.Model):
    """
    Represents a resume template configuration for a specific target role and level.

    Fields:
      - target_role: The role this template targets (e.g., 'Software Engineer').
      - target_level: The seniority level this template targets (e.g., 'II', 'Senior').
      - template_path: File path to the HTML template used for rendering.
      - style_path: File path to the CSS stylesheet used for styling.
    """

    target_role = models.CharField(
        max_length=64,
        choices=JobRole.choices,
        help_text="Target role for this template (e.g., 'Software Engineer').",
    )
    target_level = models.CharField(
        max_length=16,
        choices=JobLevel.choices,
        help_text="Target seniority level (e.g., 'II', 'Senior').",
    )
    template_path = models.CharField(
        max_length=255,
        choices=TemplatePath.choices,
        help_text="Path to the HTML template file.",
    )
    style_path = models.CharField(
        max_length=255,
        choices=StylePath.choices,
        help_text="Path to the CSS stylesheet file.",
    )

    class Meta:
        app_label = "resume"
        constraints = [
            models.UniqueConstraint(
                fields=["target_role", "target_level"],
                name="unique_role_level_template",
            )
        ]

    def __str__(self) -> str:
        return f"{self.target_role} ({self.target_level})"
