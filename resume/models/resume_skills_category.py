from django.db import models


class ResumeSkillsCategory(models.Model):
    """
    Represents a category of skills included in a generated resume.

    Fields:
      - resume: Associated resume.
      - order: Display order of this category within the resume.
      - category: Category label such as "Programming Languages" or "Data & Visualization".
      - skills_text: CSV string of related skills (e.g., "Python, Java").
      - override_text: Optional edited version of the bullet that overrides `skills_text`.
      - exclude: Whether to exclude this category from rendering.
    """

    resume = models.ForeignKey(
        "Resume",
        on_delete=models.CASCADE,
        related_name="skills_categories",
    )
    order = models.PositiveIntegerField(
        help_text="Display order of this category within the resume.",
    )
    category = models.CharField(
        max_length=255,
        help_text='Category label such as "Programming Languages" or "Data & Visualization".',
    )
    skills_text = models.TextField(
        help_text='CSV string of related skills (e.g., "Python, Java").',
    )
    override_text = models.TextField(
        blank=True,
        default="",
        help_text="Optional edited version of the bullet that overrides `skills_text`.",
    )
    exclude = models.BooleanField(
        default=False,
        help_text="Whether to exclude this category from rendering.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Category {self.order}"

    def display_text(self) -> str:
        """
        Returns the text to display, prioritizing override_text if set.
        """
        if self.override_text.strip():
            return self.override_text.strip()
        return self.skills_text.strip()