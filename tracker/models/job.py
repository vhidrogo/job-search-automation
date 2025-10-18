from __future__ import annotations
from typing import Iterable, List, Optional
from django.core.validators import MinValueValidator
from django.db import models

from resume.schemas.jd_schema import Metadata


class JobRole(models.TextChoices):
    ANALYTICS_ENGINEER = "Analytics Engineer"
    BUSINESS_ANALYST = "Business Analyst"
    BUSINESS_INTELLIGENCE_ENGINEER = "Business Intelligence Engineer"
    DATA_ANALYST = "Data Analyst"
    DATA_ENGINEER = "Data Engineer"
    SOFTWARE_ENGINEER = "Software Engineer"


class JobLevel(models.TextChoices):
    I = "I"
    II = "II"
    III = "III"
    SENIOR = "Senior"


class WorkSetting(models.TextChoices):
    ON_SITE = "On-site"
    HYBRID = "Hybrid"
    REMOTE = "Remote"


class Job(models.Model):
    """
    Represents a job listing parsed from a job description.

    Fields:
      - company: Name of the employer.
      - listing_job_title: Job title as listed in the job description.
      - role: Standardized role classification (e.g., 'Software Engineer').
      - specialization: Optional area of specialization for the role.
      - level: Optional seniority or level designation (e.g., 'II', 'Senior').
      - location: Optional location string.
      - work_setting: Work arrangement (e.g., 'Remote', 'On-site', 'Hybrid').
      - min_experience_years: Minimum experience required for the role.
      - min_salary / max_salary: Optional salary bounds.
    """

    company = models.CharField(max_length=255, db_index=True)
    listing_job_title = models.CharField(max_length=255, db_index=True)
    role = models.CharField(max_length=64, choices=JobRole.choices, db_index=True)
    specialization = models.CharField(max_length=128, blank=True, null=True)
    level = models.CharField(max_length=16, choices=JobLevel.choices)
    location = models.CharField(max_length=255)
    work_setting = models.CharField(max_length=16, choices=WorkSetting.choices)

    min_experience_years = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Minimum years of experience (nullable if not parsed).",
    )

    min_salary = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Minimum salary in the job listing (nullable).",
    )
    max_salary = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Maximum salary in the job listing (nullable).",
    )

    class Meta:
        app_label = "tracker"
        indexes = [
            models.Index(fields=["company", "role"]),
        ]

    def __str__(self) -> str:
        return f"{self.company} — {self.listing_job_title} ({self.role})"

    def salary_range(self) -> Optional[str]:
        """
        Human-friendly salary range, or None if not provided.
        """
        if self.min_salary is None and self.max_salary is None:
            return None
        if self.min_salary is None:
            return f"<= {self.max_salary}"
        if self.max_salary is None:
            return f">= {self.min_salary}"
        return f"{self.min_salary:,} - {self.max_salary:,}"

    @classmethod
    def bulk_create_from_parsed(
        cls, parsed_jobs: List["Metadata"], batch_size: int = 100
    ) -> List["Job"]:
        """
        Bulk-create Job records from a sequence of Metadata Pydantic models.
        Returns the list of created Job instances.
        """
        objs: List[Job] = []
        for pj in parsed_jobs:
            objs.append(
                cls(
                    company=pj.company,
                    listing_job_title=pj.listing_job_title,
                    role=pj.role,
                    specialization=pj.specialization,
                    level=pj.level,
                    location=pj.location,
                    work_setting=pj.work_setting,
                    min_experience_years=pj.min_experience_years,
                    min_salary=pj.min_salary,
                    max_salary=pj.max_salary,
                )
            )
        created = cls.objects.bulk_create(objs, batch_size=batch_size)
        return created
