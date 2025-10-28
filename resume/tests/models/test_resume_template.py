from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from resume.models import ResumeTemplate
from tracker.models.job import JobLevel, JobRole


class TestResumeTemplateModel(TestCase):
    """Test suite for the ResumeTemplate model."""

    TARGET_ROLE = JobRole.SOFTWARE_ENGINEER
    TARGET_LEVEL = JobLevel.II
    TEMPLATE_PATH = "templates/software_engineer_ii.html"
    STYLE_PATH = "css/resume.css"
    ALT_TARGET_ROLE = JobRole.DATA_ENGINEER
    ALT_TARGET_LEVEL = JobLevel.SENIOR
    ALT_TEMPLATE_PATH = "templates/data_engineer_senior.html"
    ALT_STYLE_PATH = "css/resume_alt.css"

    def test_create_resume_template(self) -> None:
        """Test creating a ResumeTemplate instance."""
        template = ResumeTemplate.objects.create(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            template_path=self.TEMPLATE_PATH,
            style_path=self.STYLE_PATH,
        )

        self.assertEqual(template.target_role, self.TARGET_ROLE)
        self.assertEqual(template.target_level, self.TARGET_LEVEL)
        self.assertEqual(template.template_path, self.TEMPLATE_PATH)
        self.assertEqual(template.style_path, self.STYLE_PATH)
        self.assertIsNotNone(template.id)

    def test_str_representation(self) -> None:
        """Test the string representation of ResumeTemplate."""
        template = ResumeTemplate.objects.create(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            template_path=self.TEMPLATE_PATH,
            style_path=self.STYLE_PATH,
        )

        self.assertEqual(
            str(template),
            "Software Engineer (II)",
        )

    def test_unique_constraint_on_role_and_level(self) -> None:
        """Test that duplicate role and level combinations are rejected."""
        ResumeTemplate.objects.create(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            template_path=self.TEMPLATE_PATH,
            style_path=self.STYLE_PATH,
        )

        with self.assertRaises(IntegrityError):
            ResumeTemplate.objects.create(
                target_role=self.TARGET_ROLE,
                target_level=self.TARGET_LEVEL,
                template_path="templates/another_path.html",
                style_path="css/another_style.css",
            )

    def test_different_role_same_level_allowed(self) -> None:
        """Test that different roles with the same level are allowed."""
        ResumeTemplate.objects.create(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            template_path=self.TEMPLATE_PATH,
            style_path=self.STYLE_PATH,
        )

        template2 = ResumeTemplate.objects.create(
            target_role=self.ALT_TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            template_path=self.ALT_TEMPLATE_PATH,
            style_path=self.ALT_STYLE_PATH,
        )

        self.assertEqual(ResumeTemplate.objects.count(), 2)
        self.assertEqual(template2.target_role, self.ALT_TARGET_ROLE)

    def test_same_role_different_level_allowed(self) -> None:
        """Test that the same role with different levels are allowed."""
        ResumeTemplate.objects.create(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            template_path=self.TEMPLATE_PATH,
            style_path=self.STYLE_PATH,
        )

        template2 = ResumeTemplate.objects.create(
            target_role=self.TARGET_ROLE,
            target_level=self.ALT_TARGET_LEVEL,
            template_path=self.ALT_TEMPLATE_PATH,
            style_path=self.ALT_STYLE_PATH,
        )

        self.assertEqual(ResumeTemplate.objects.count(), 2)
        self.assertEqual(template2.target_level, self.ALT_TARGET_LEVEL)

    def test_query_by_role_and_level(self) -> None:
        """Test querying by role and level."""
        ResumeTemplate.objects.create(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            template_path=self.TEMPLATE_PATH,
            style_path=self.STYLE_PATH,
        )

        template = ResumeTemplate.objects.get(
            target_role=self.TARGET_ROLE, target_level=self.TARGET_LEVEL
        )

        self.assertEqual(template.template_path, self.TEMPLATE_PATH)
        self.assertEqual(template.style_path, self.STYLE_PATH)

    def test_invalid_role_choice(self) -> None:
        """Test that invalid role choices are rejected."""
        template = ResumeTemplate(
            target_role="Invalid Role",
            target_level=self.TARGET_LEVEL,
            template_path=self.TEMPLATE_PATH,
            style_path=self.STYLE_PATH,
        )

        with self.assertRaises(ValidationError):
            template.full_clean()

    def test_invalid_level_choice(self) -> None:
        """Test that invalid level choices are rejected."""
        template = ResumeTemplate(
            target_role=self.TARGET_ROLE,
            target_level="Invalid Level",
            template_path=self.TEMPLATE_PATH,
            style_path=self.STYLE_PATH,
        )

        with self.assertRaises(ValidationError):
            template.full_clean()

    def test_empty_template_path_not_allowed(self) -> None:
        """Test that empty template_path is rejected."""
        template = ResumeTemplate(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            template_path="",
            style_path=self.STYLE_PATH,
        )

        with self.assertRaises(ValidationError):
            template.full_clean()

    def test_empty_style_path_not_allowed(self) -> None:
        """Test that empty style_path is rejected."""
        template = ResumeTemplate(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            template_path=self.TEMPLATE_PATH,
            style_path="",
        )

        with self.assertRaises(ValidationError):
            template.full_clean()
