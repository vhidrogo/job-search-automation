from django.db import models

from tracker.models.job import JobLevel, JobRole


class ResumeTemplate(models.Model):
    """
    Represents a resume template configuration for a specific target role and level.

    Fields:
      - target_role: The role this template targets (e.g., 'Software Engineer').
      - target_level: The seniority level this template targets (e.g., 'II', 'Senior').
      - template_path: File path to the Markdown template used for rendering.
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
        help_text="Path to the Markdown template file.",
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
        return f"{self.target_role} ({self.target_level}) — {self.template_path}"
