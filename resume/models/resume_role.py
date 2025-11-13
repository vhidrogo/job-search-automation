from django.db import models


class ResumeRole(models.Model):
    """
    Represents a frozen copy of an experience role within a generated resume.

    Fields:
      - resume: Associated resume.
      - source_role: Original experience role used as the source.
      - title: Frozen title used in this resume (copied from override_title or source_role.title).
      - order: Display order of this role within the resume.
    """

    resume = models.ForeignKey(
        "Resume",
        on_delete=models.CASCADE,
        related_name="experience_roles",
    )
    source_role = models.ForeignKey(
        "ExperienceRole",
        on_delete=models.PROTECT,
        help_text="Original experience role used as the source.",
    )
    title = models.CharField(
        max_length=255,
        help_text="Frozen title used in this resume (copied from override_title or source_role.title).",
    )
    order = models.PositiveIntegerField(
        help_text="Display order of this role within the resume.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["resume", "source_role"],
                name="unique_resume_source_role",
            ),
        ]

    def __str__(self):
        return f"Role {self.order}"
