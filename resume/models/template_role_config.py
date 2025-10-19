# resume/models/template_role_config.py
from django.db import models


class TemplateRoleConfig(models.Model):
    """
    Represents configuration for an experience role within a resume template.

    Fields:
      - template: The resume template this configuration belongs to.
      - experience_role: The experience role to include in the template.
      - include: Whether to include this role when rendering the template.
      - max_bullet_count: Maximum number of bullets to generate for this role.
    """

    template = models.ForeignKey(
        "ResumeTemplate",
        on_delete=models.CASCADE,
        related_name="role_configs",
        help_text="The resume template this configuration belongs to.",
    )
    experience_role = models.ForeignKey(
        "ExperienceRole",
        on_delete=models.CASCADE,
        related_name="template_configs",
        help_text="The experience role to configure for this template.",
    )
    include = models.BooleanField(
        default=True,
        help_text="Whether to include this role when rendering the template.",
    )
    max_bullet_count = models.PositiveIntegerField(
        help_text="Maximum number of bullets to generate for this role.",
    )

    class Meta:
        app_label = "resume"
        constraints = [
            models.UniqueConstraint(
                fields=["template", "experience_role"],
                name="unique_template_experience_role",
            )
        ]

    def __str__(self) -> str:
        return f"{self.template.target_role} ({self.template.target_level}) — {self.experience_role.key}"
