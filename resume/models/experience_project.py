from django.db import models


class ExperienceProject(models.Model):
    """
    Represents a project or task completed during a specific work role.

    Fields:
      - experience_role: The associated role during which this project was completed.
      - short_name: Short label for the project or task.
      - problem_context: Concise problem statement describing the challenge addressed.
      - actions: List of action items ["implemented X", "rewrote Y"].
      - tools: Comma-separated list of tools/technologies used (e.g., "Django,Postgres").
      - outcomes: Comma-separated list of short outcomes (e.g., "reduced latency 80%").
      - impact_area: Category describing the type of impact (e.g., "Performance Optimization").
    """

    experience_role = models.ForeignKey(
        "ExperienceRole",
        on_delete=models.CASCADE,
        related_name="projects",
        help_text="The role during which this project was completed.",
    )
    short_name = models.CharField(
        max_length=255,
        help_text="Short label for the project/task (e.g., 'Search API Redesign').",
    )
    problem_context = models.TextField(
        help_text="Concise problem statement describing the challenge addressed.",
    )
    actions = models.JSONField(default=list)
    tools = models.JSONField(default=list)
    outcomes = models.JSONField(default=list)
    impact_area = models.CharField(
        max_length=255,
        help_text="Category describing the type of impact (e.g., 'Performance Optimization', 'User Engagement').",
    )

    class Meta:
        app_label = "resume"

    def __str__(self) -> str:
        return f"{self.short_name} ({self.experience_role})"
