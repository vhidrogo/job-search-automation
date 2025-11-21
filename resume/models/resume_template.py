from django.db import models

from tracker.models.job import JobLevel, JobRole


class TemplatePath(models.TextChoices):
    """
    Enum of available HTML resume templates.

    Paths are relative to the template directory (not absolute file system paths).
    """
    ANALYST = "html/analyst.html", "Analyst"
    ENGINEER = "html/engineer.html", "Engineer"


class StylePath(models.TextChoices):
    """
    Enum of available CSS stylesheet options for resume templates.

    Paths are relative to the static directory (not absolute file system paths).
    """
    COMPACT = "css/resume_compact.css", "Compact"
    DENSE = "css/resume_dense.css", "Dense"
    STANDARD = "css/resume_standard.css", "Standard"


class TargetSpecialization(models.TextChoices):
    BACKEND = "backend", "Backend"
    FULL_STACK = "fullstack", "Full-Stack"
    PYTHON = "python", "Python"


class ResumeTemplate(models.Model):
    """
    Represents a resume template configuration for a specific target role, level, and optional specialization.

    Fields:
      - target_role: The role this template targets (e.g., 'Software Engineer').
      - target_level: The seniority level this template targets (e.g., 'II', 'Senior').
      - target_specialization: Optional specialization within the role (e.g., 'Backend', 'Python').
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
    target_specialization = models.CharField(
        max_length=16,
        choices=TargetSpecialization.choices,
        help_text="Optional specialization (e.g., 'Backend', 'Python').",
        null=True,
        blank=True,
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
    is_custom = models.BooleanField(
        default=False,
        help_text="Whether this is a custom one-off template vs. a standard reusable template",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Description for custom templates (e.g., 'SWE II with BI experience')",
    )

    class Meta:
        app_label = "resume"
        constraints = [
            models.UniqueConstraint(
                fields=["target_role", "target_level", "target_specialization"],
                condition=models.Q(is_custom=False),
                name="unique_role_level_specialization",
            ),
            models.UniqueConstraint(
                fields=["target_role", "target_level"],
                condition=models.Q(is_custom=False, target_specialization__isnull=True),
                name="unique_role_level_no_specialization",
            ),
        ]

    def __str__(self):
        if self.is_custom:
            return f"Custom: {self.description}"
        specialization = f" ({self.get_target_specialization_display()})" if self.target_specialization else ""
        return f"{self.get_target_role_display()} {self.get_target_level_display()}{specialization}"
