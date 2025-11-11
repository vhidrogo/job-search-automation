from django.db import models


class ResumeSkillBullet(models.Model):
    """
    Represents a single skill category and its associated skills for a resume.

    Fields:
      - resume: The resume this skill bullet belongs to.
      - category: Category label such as "Programming Languages" or "Data & Visualization".
      - skills_text: CSV string of related skills (e.g., "Python, Java").
    """

    resume = models.ForeignKey(
        "Resume",
        on_delete=models.CASCADE,
        related_name="skill_bullets",
        help_text="Resume this skill bullet belongs to.",
    )
    category = models.CharField(
        max_length=255,
        help_text="Category label such as 'Programming Languages' or 'Data & Visualization'.",
    )
    skills_text = models.TextField(
        help_text="CSV string of related skills (e.g., 'Python, Java').",
    )
    exclude = models.BooleanField(
        default=False,
        help_text="Whether to exclude this skills category from the rendered resume.",
    )

    class Meta:
        app_label = "resume"

    def __str__(self) -> str:
        skills_preview = self.skills_list_display()[:50]
        return f"{self.category} for {self.resume.job.company}: {skills_preview}..."

    def skills_list_display(self) -> str:
        """
        Returns the skills text for display.
        """
        return self.skills_text.strip()

    def skills_list(self) -> list[str]:
        """
        Returns skills as a list of strings, stripping whitespace from each skill.
        """
        if not self.skills_text.strip():
            return []
        return [skill.strip() for skill in self.skills_text.split(",") if skill.strip()]
