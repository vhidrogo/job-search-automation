from django.db import models


class ResumeExperienceBullet(models.Model):
    """
    Represents a single experience bullet point for a resume.

    Fields:
      - resume: The resume this bullet belongs to.
      - experience_role: The experience role this bullet was generated for.
      - role_order: Role display order within the resume.
      - role_bullet_order: Bullet display order within the role.
      - text: The generated bullet content.
      - exclude: Whether to exclude this bullet from the rendered resume.
      - override_text: Optional manually edited version that takes priority over text.
    """

    resume = models.ForeignKey(
        "Resume",
        on_delete=models.CASCADE,
        related_name="experience_bullets",
        help_text="Resume this bullet belongs to.",
    )
    experience_role = models.ForeignKey(
        "ExperienceRole",
        on_delete=models.CASCADE,
        related_name="resume_bullets",
        help_text="Experience role this bullet was generated for.",
    )
    role_order = models.PositiveIntegerField(
        help_text="Role order within the resume.",
    )
    role_bullet_order = models.PositiveIntegerField(
        help_text="Bullet display order within the role.",
    )
    text = models.TextField(
        help_text="Generated bullet content.",
    )
    exclude = models.BooleanField(
        default=False,
        help_text="Whether to exclude this bullet from the rendered resume.",
    )
    override_text = models.TextField(
        blank=True,
        default="",
        help_text="Optional manually edited version that takes priority over text.",
    )

    class Meta:
        ordering = ["role_order", "role_bullet_order"]
        indexes = [
            models.Index(fields=["resume", "role_order", "role_bullet_order"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["resume", "role_order", "role_bullet_order"],
                name="unique_resume_role_order_role_bullet_order",
            )
        ]

    def __str__(self) -> str:
        bullet_preview = self.display_text()[:50]
        excluded_marker = " [EXCLUDED]" if self.exclude else ""
        return f"Bullet {self.role_order}.{self.role_bullet_order} for {self.resume.job.company}{excluded_marker}: {bullet_preview}..."

    def display_text(self) -> str:
        """
        Returns the text to display, prioritizing override_text if set.
        """
        if self.override_text.strip():
            return self.override_text.strip()
        return self.text.strip()
