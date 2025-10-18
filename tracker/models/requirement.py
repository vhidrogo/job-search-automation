from __future__ import annotations
from typing import List
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .job import Job
from resume.schemas.jd_schema import RequirementSchema


class Requirement(models.Model):
    """
    Represents a single parsed requirement extracted from a job description.

    Fields:
      - job: FK to the Job this requirement was extracted from.
      - text: The human-readable requirement text (e.g., "Strong Python skills").
      - keywords: List of short tokenized keywords or concepts associated with the requirement.
      - relevance: Float in [0, 1] representing how important/relevant this requirement is.
      - order: Integer ordering of the requirement as returned by the parser (lower = earlier).
    """

    job = models.ForeignKey("tracker.Job", on_delete=models.CASCADE, related_name="requirements")
    text = models.TextField()
    keywords = models.JSONField(default=list)
    relevance = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Relevance score in the range [0.0, 1.0].",
    )
    order = models.PositiveIntegerField(help_text="Ordering index from the parser.")

    class Meta:
        app_label = "tracker"
        indexes = [
            models.Index(fields=["job", "relevance"]),
            models.Index(fields=["job", "order"]),
        ]
        ordering = ["job", "order"]

    def __str__(self) -> str:
        return f"Requirement(job_id={self.job_id}, order={self.order}, relevance={self.relevance})"

    @classmethod
    def bulk_create_from_parsed(cls, job: "Job", parsed_requirements: List[RequirementSchema], batch_size: int = 100) -> List["Requirement"]:
        """
        Bulk-create Requirement records from a sequence of RequirementSchema Pydantic models.

        Args:
            parsed_requirements: Sequence of RequirementSchema instances (validated).
            batch_size: Passed to QuerySet.bulk_create for efficient inserts.

        Returns:
            List of created Requirement instances (as returned by bulk_create).
        """
        if not parsed_requirements:
            return []

        objs: List[Requirement] = []
        for pr in parsed_requirements:
            objs.append(
                cls(
                    job=job,
                    text=pr.text,
                    keywords=pr.keywords,
                    relevance=pr.relevance,
                    order=pr.order,
                )
            )
        created = cls.objects.bulk_create(objs, batch_size=batch_size)
        return created
