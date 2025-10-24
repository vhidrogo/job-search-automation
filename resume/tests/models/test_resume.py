from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from resume.models import Resume, ResumeTemplate
from tracker.models.job import Job, JobLevel, JobRole, WorkSetting


class TestResumeModelBasics(TestCase):
    """Test suite for the Resume model."""

    COMPANY = "Meta"
    LISTING_JOB_TITLE = "Software Engineer"
    ROLE = JobRole.SOFTWARE_ENGINEER
    LEVEL = JobLevel.II
    LOCATION = "Seattle, WA"
    WORK_SETTING = WorkSetting.REMOTE
    MIN_EXPERIENCE_YEARS = 3
    TEMPLATE_PATH = "templates/software_engineer_ii.md"
    UNMET_REQUIREMENTS = "Go,Ruby on Rails"
    MATCH_RATIO = 0.85

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.template = ResumeTemplate.objects.create(
            target_role=self.ROLE,
            target_level=self.LEVEL,
            template_path=self.TEMPLATE_PATH,
        )
        self.job = Job.objects.create(
            company=self.COMPANY,
            listing_job_title=self.LISTING_JOB_TITLE,
            role=self.ROLE,
            level=self.LEVEL,
            location=self.LOCATION,
            work_setting=self.WORK_SETTING,
            min_experience_years=self.MIN_EXPERIENCE_YEARS,
        )

    def test_create_resume(self) -> None:
        """Test creating a Resume instance."""
        resume = Resume.objects.create(
            template=self.template,
            job=self.job,
            unmet_requirements=self.UNMET_REQUIREMENTS,
            match_ratio=self.MATCH_RATIO,
        )

        self.assertEqual(resume.template, self.template)
        self.assertEqual(resume.job, self.job)
        self.assertEqual(resume.unmet_requirements, self.UNMET_REQUIREMENTS)
        self.assertEqual(resume.match_ratio, self.MATCH_RATIO)
        self.assertIsNotNone(resume.id)

    def test_str_representation(self) -> None:
        """Test the string representation of Resume."""
        resume = Resume.objects.create(
            template=self.template,
            job=self.job,
            match_ratio=self.MATCH_RATIO,
        )

        self.assertEqual(str(resume), "Resume for Meta — Software Engineer (match: 85%)")

    def test_default_values(self) -> None:
        """Test default field values."""
        resume = Resume.objects.create(
            template=self.template,
            job=self.job,
        )

        self.assertEqual(resume.unmet_requirements, "")
        self.assertEqual(resume.match_ratio, 0.0)

    def test_match_percentage_formatting(self) -> None:
        """Test match_percentage() helper method."""
        resume = Resume.objects.create(
            template=self.template,
            job=self.job,
            match_ratio=0.8567,
        )

        self.assertEqual(resume.match_percentage(), "86%")

    def test_match_percentage_zero(self) -> None:
        """Test match_percentage() with zero match."""
        resume = Resume.objects.create(
            template=self.template,
            job=self.job,
            match_ratio=0.0,
        )

        self.assertEqual(resume.match_percentage(), "0%")

    def test_match_percentage_full(self) -> None:
        """Test match_percentage() with perfect match."""
        resume = Resume.objects.create(
            template=self.template,
            job=self.job,
            match_ratio=1.0,
        )

        self.assertEqual(resume.match_percentage(), "100%")

    def test_unmet_list_with_requirements(self) -> None:
        """Test unmet_list() returns parsed list."""
        resume = Resume.objects.create(
            template=self.template,
            job=self.job,
            unmet_requirements=self.UNMET_REQUIREMENTS,
        )

        unmet = resume.unmet_list()
        self.assertIsNotNone(unmet)
        self.assertEqual(unmet, ["Go", "Ruby on Rails"])

    def test_unmet_list_empty(self) -> None:
        """Test unmet_list() returns None when empty."""
        resume = Resume.objects.create(
            template=self.template,
            job=self.job,
            unmet_requirements="",
        )

        self.assertIsNone(resume.unmet_list())

    def test_unmet_list_whitespace_only(self) -> None:
        """Test unmet_list() handles whitespace-only string."""
        resume = Resume.objects.create(
            template=self.template,
            job=self.job,
            unmet_requirements="   ",
        )

        self.assertIsNone(resume.unmet_list())

    def test_unmet_list_with_extra_whitespace(self) -> None:
        """Test unmet_list() strips whitespace around entries."""
        resume = Resume.objects.create(
            template=self.template,
            job=self.job,
            unmet_requirements="Go , Ruby on Rails,  Kotlin  ",
        )

        unmet = resume.unmet_list()
        self.assertEqual(unmet, ["Go", "Ruby on Rails", "Kotlin"])

    def test_match_ratio_below_zero_validation(self) -> None:
        """Test that match_ratio below 0.0 is rejected."""
        resume = Resume(
            template=self.template,
            job=self.job,
            match_ratio=-0.1,
        )

        with self.assertRaises(ValidationError):
            resume.full_clean()

    def test_match_ratio_above_one_validation(self) -> None:
        """Test that match_ratio above 1.0 is rejected."""
        resume = Resume(
            template=self.template,
            job=self.job,
            match_ratio=1.5,
        )

        with self.assertRaises(ValidationError):
            resume.full_clean()

    def test_one_resume_per_job_constraint(self) -> None:
        """Test that only one resume can be created per job."""
        Resume.objects.create(
            template=self.template,
            job=self.job,
            match_ratio=0.75,
        )

        with self.assertRaises(IntegrityError):
            Resume.objects.create(
                template=self.template,
                job=self.job,
                match_ratio=0.85,
            )

    def test_cascade_delete_on_template_deletion(self) -> None:
        """Test that deleting template cascades to resumes."""
        Resume.objects.create(
            template=self.template,
            job=self.job,
        )

        self.assertEqual(Resume.objects.count(), 1)
        self.template.delete()
        self.assertEqual(Resume.objects.count(), 0)

    def test_cascade_delete_on_job_deletion(self) -> None:
        """Test that deleting job cascades to resumes."""
        Resume.objects.create(
            template=self.template,
            job=self.job,
        )

        self.assertEqual(Resume.objects.count(), 1)
        self.job.delete()
        self.assertEqual(Resume.objects.count(), 0)

    def test_related_name_from_template(self) -> None:
        """Test accessing resumes from template via related_name."""
        resume = Resume.objects.create(
            template=self.template,
            job=self.job,
        )

        self.assertIn(resume, self.template.resumes.all())

    def test_related_name_from_job(self) -> None:
        """Test accessing resume from job via related_name."""
        resume = Resume.objects.create(
            template=self.template,
            job=self.job,
        )

        self.assertEqual(self.job.resume, resume)

    def test_query_by_job_and_template(self) -> None:
        """Test querying resumes by job and template."""
        resume = Resume.objects.create(
            template=self.template,
            job=self.job,
            match_ratio=self.MATCH_RATIO,
        )

        retrieved = Resume.objects.get(job=self.job, template=self.template)
        self.assertEqual(retrieved.id, resume.id)
        self.assertEqual(retrieved.match_ratio, self.MATCH_RATIO)
