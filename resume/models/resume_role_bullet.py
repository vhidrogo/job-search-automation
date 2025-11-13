from django.db import models


class ResumeRoleBullet(models.Model):
    """
    Represents a generated or edited experience bullet tied to a specific role in a resume.

    Fields:
      - resume_role: The associated ResumeRole.
      - text: Original bullet content.
      - override_text: Optional edited version of the bullet that overrides `text`.
      - order: Display order within the role.
      - exclude: Whether to exclude this bullet from the rendered resume.
    """

    resume_role = models.ForeignKey(
        "ResumeRole",
        on_delete=models.CASCADE,
        related_name="bullets",
    )
    text = models.TextField(
        help_text="Original bullet content.",
    )
    override_text = models.TextField(
        blank=True,
        default="",
        help_text="Optional edited version of the bullet that overrides `text`.",
    )
    order = models.PositiveIntegerField(
        help_text="Display order within the role.",
    )
    exclude = models.BooleanField(
        default=False,
        help_text="Whether to exclude this bullet from the rendered resume.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["resume_role", "order"],
                name="unique_resume_role_order",
            ),
        ]

    def __str__(self):
        return f"Bullet {self.order}"

    def display_text(self) -> str:
        """
        Returns the text to display, prioritizing override_text if set.
        """
        if self.override_text.strip():
            return self.override_text.strip()
        return self.text.strip()
