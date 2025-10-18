from typing import Optional

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Resume(models.Model):
    """
    Represents a generated resume for a specific job application.

    Fields:
      - template: The ResumeTemplate used to render this resume.
      - job: The job listing this resume targets.
      - unmet_requirements: CSV string of tools/technologies not covered by this resume.
      - match_ratio: Fraction of requirements met by this resume (0.0 to 1.0).
    """

    template = models.ForeignKey(
        "resume.ResumeTemplate",
        on_delete=models.CASCADE,
        related_name="resumes",
        help_text="Template used to generate this resume.",
    )
    job = models.OneToOneField(
        "tracker.Job",
        on_delete=models.CASCADE,
        related_name="resume",
        help_text="Job listing this resume targets.",
    )
    unmet_requirements = models.TextField(
        blank=True,
        default="",
        help_text="CSV string of unmatched tools/technologies (e.g., 'Go,Ruby on Rails').",
    )
    match_ratio = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Fraction of requirements met (0.0 to 1.0).",
    )

    class Meta:
        app_label = "resume"
        indexes = [
            models.Index(fields=["template"]),
        ]

    def __str__(self) -> str:
        return f"Resume for {self.job.company} — {self.job.listing_job_title} (match: {self.match_ratio:.0%})"

    def match_percentage(self) -> str:
        """
        Human-friendly match ratio as percentage string.
        """
        return f"{self.match_ratio * 100:.0f}%"

    def unmet_list(self) -> Optional[list[str]]:
        """
        Returns unmet requirements as a list of strings, or None if empty.
        """
        if not self.unmet_requirements.strip():
            return None
        return [req.strip() for req in self.unmet_requirements.split(",") if req.strip()]