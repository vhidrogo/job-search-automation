from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from pathlib import Path
from unittest.mock import MagicMock, patch

from resume.models import (
    ExperienceRole,
    Resume,
    ResumeExperienceBullet,
    ResumeSkillBullet,
    ResumeTemplate,
    TemplateRoleConfig,
)
from tracker.models import Job, JobLevel, JobRole, WorkSetting


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


class TestResumeRenderToPDF(TestCase):
    """Test suite for Resume.render_to_pdf() and helper methods."""

    COMPANY = "Meta"
    LISTING_JOB_TITLE = "Software Engineer"
    ROLE = JobRole.SOFTWARE_ENGINEER
    LEVEL = JobLevel.II
    LOCATION = "Seattle, WA"
    WORK_SETTING = WorkSetting.REMOTE
    TEMPLATE_PATH = "templates/software_engineer_ii.html"
    OUTPUT_DIR = "test_output/resumes"

    def setUp(self) -> None:
        self.patcher_html = patch("resume.models.resume.HTML")
        self.patcher_render = patch("resume.models.resume.render_to_string")
        self.patcher_path = patch("resume.models.resume.Path")
        
        self.mock_html = self.patcher_html.start()
        self.mock_render = self.patcher_render.start()
        self.mock_path = self.patcher_path.start()
        
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
        )
        self.resume = Resume.objects.create(
            template=self.template,
            job=self.job,
            match_ratio=0.85,
        )

        self.role1 = ExperienceRole.objects.create(
            key="navit_swe",
            company="Nav.it",
            title="Software Engineer",
        )
        self.role2 = ExperienceRole.objects.create(
            key="amazon_sde",
            company="Amazon",
            title="Software Development Engineer",
        )

    def tearDown(self) -> None:
        self.patcher_html.stop()
        self.patcher_render.stop()
        self.patcher_path.stop()

    def test_sanitize_filename_replaces_spaces_with_underscores(self) -> None:
        """Test filename sanitization replaces spaces."""
        result = self.resume._sanitize_filename("Software Engineer")
        self.assertEqual(result, "Software_Engineer")

    def test_sanitize_filename_removes_special_characters(self) -> None:
        """Test filename sanitization removes special characters."""
        result = self.resume._sanitize_filename("C++ / C# Developer!")
        self.assertEqual(result, "C__C_Developer")

    def test_sanitize_filename_preserves_alphanumeric_and_hyphens(self) -> None:
        """Test filename sanitization preserves valid characters."""
        result = self.resume._sanitize_filename("Data-Engineer-II")
        self.assertEqual(result, "Data-Engineer-II")

    def test_generate_pdf_filename(self) -> None:
        """Test PDF filename generation."""
        result = self.resume._generate_pdf_filename()
        self.assertEqual(result, "Meta_Software_Engineer.pdf")

    def test_generate_pdf_filename_with_special_characters(self) -> None:
        """Test PDF filename generation with special characters."""
        job = Job.objects.create(
            company="Jane's Corp.",
            listing_job_title="C++ Developer (Senior)",
            role=self.ROLE,
            level=self.LEVEL,
            location=self.LOCATION,
            work_setting=self.WORK_SETTING,
        )
        resume = Resume.objects.create(
            template=self.template,
            job=job,
        )
        
        result = resume._generate_pdf_filename()
        self.assertEqual(result, "Janes_Corp_C_Developer_Senior.pdf")

    def test_get_template_name(self) -> None:
        """Test template name generation."""
        result = self.resume._get_template_name()
        self.assertEqual(result, "html/software_engineer_ii.html")

    def test_get_template_name_with_spaces(self) -> None:
        """Test template name generation with spaces in role/level."""
        template = ResumeTemplate.objects.create(
            target_role=JobRole.DATA_ENGINEER,
            target_level=JobLevel.SENIOR,
            template_path="templates/data_engineer_senior.html",
        )
        job = Job.objects.create(
            company="TestCo",
            listing_job_title="Data Engineer",
            role=JobRole.DATA_ENGINEER,
            level=JobLevel.SENIOR,
            location=self.LOCATION,
            work_setting=self.WORK_SETTING,
        )
        resume = Resume.objects.create(
            template=template,
            job=job,
        )
        
        result = resume._get_template_name()
        self.assertEqual(result, "html/data_engineer_senior.html")

    def test_render_role_bullets_returns_empty_for_no_bullets(self) -> None:
        """Test rendering role bullets returns empty string when no bullets exist."""
        result = self.resume._render_role_bullets(self.role1)
        self.assertEqual(result, "")

    def test_render_role_bullets_returns_html_list_items(self) -> None:
        """Test rendering role bullets returns properly formatted HTML."""
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role1,
            order=1,
            text="Implemented feature X using Django",
        )
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role1,
            order=2,
            text="Reduced latency by 80%",
        )

        result = self.resume._render_role_bullets(self.role1)

        self.assertIn("<li>Implemented feature X using Django</li>", result)
        self.assertIn("<li>Reduced latency by 80%</li>", result)

    def test_render_role_bullets_excludes_marked_bullets(self) -> None:
        """Test that bullets marked as excluded are filtered out."""
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role1,
            order=1,
            text="Included bullet",
            exclude=False,
        )
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role1,
            order=2,
            text="Excluded bullet",
            exclude=True,
        )

        result = self.resume._render_role_bullets(self.role1)

        self.assertIn("<li>Included bullet</li>", result)
        self.assertNotIn("Excluded bullet", result)

    def test_render_role_bullets_uses_override_text_when_present(self) -> None:
        """Test that override_text is used instead of text when set."""
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role1,
            order=1,
            text="Original text",
            override_text="Overridden text",
        )

        result = self.resume._render_role_bullets(self.role1)

        self.assertIn("<li>Overridden text</li>", result)
        self.assertNotIn("Original text", result)

    def test_render_role_bullets_respects_order(self) -> None:
        """Test that bullets are rendered in correct order."""
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role1,
            order=2,
            text="Second bullet",
        )
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role1,
            order=1,
            text="First bullet",
        )

        result = self.resume._render_role_bullets(self.role1)

        first_pos = result.index("First bullet")
        second_pos = result.index("Second bullet")
        self.assertLess(first_pos, second_pos)

    def test_render_skills_returns_empty_for_no_skills(self) -> None:
        """Test rendering skills returns empty string when no skills exist."""
        result = self.resume._render_skills()
        self.assertEqual(result, "")

    def test_render_skills_returns_formatted_html(self) -> None:
        """Test rendering skills returns properly formatted HTML."""
        ResumeSkillBullet.objects.create(
            resume=self.resume,
            category="Programming Languages",
            skills_text="Python, Java, JavaScript",
        )
        ResumeSkillBullet.objects.create(
            resume=self.resume,
            category="Databases",
            skills_text="PostgreSQL, MongoDB",
        )

        result = self.resume._render_skills()

        self.assertIn('<strong>Programming Languages:</strong> Python, Java, JavaScript', result)
        self.assertIn('<strong>Databases:</strong> PostgreSQL, MongoDB', result)
        self.assertIn('class="skill-category"', result)

    def test_build_template_context_with_two_roles(self) -> None:
        """Test building template context with two configured roles."""
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role1,
            order=1,
            max_bullet_count=3,
        )
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role2,
            order=2,
            max_bullet_count=3,
        )
        
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role1,
            order=1,
            text="First role bullet",
        )
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role2,
            order=1,
            text="Second role bullet",
        )
        
        ResumeSkillBullet.objects.create(
            resume=self.resume,
            category="Languages",
            skills_text="Python",
        )

        context = self.resume._build_template_context()

        self.assertIn("first_role_bullets", context)
        self.assertIn("second_role_bullets", context)
        self.assertIn("skills", context)
        self.assertIn("First role bullet", context["first_role_bullets"])
        self.assertIn("Second role bullet", context["second_role_bullets"])
        self.assertIn("Languages", context["skills"])

    def test_build_template_context_respects_role_order(self) -> None:
        """Test that role configs are processed in correct order."""
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role2,
            order=1,
            max_bullet_count=3,
        )
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role1,
            order=2,
            max_bullet_count=3,
        )
        
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role1,
            order=1,
            text="Role 1 bullet",
        )
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role2,
            order=1,
            text="Role 2 bullet",
        )

        context = self.resume._build_template_context()

        self.assertIn("Role 2 bullet", context["first_role_bullets"])
        self.assertIn("Role 1 bullet", context["second_role_bullets"])

    def test_build_template_context_handles_more_than_six_roles(self) -> None:
        """Test that roles beyond sixth use numeric suffixes."""
        roles = []
        for i in range(7):
            role = ExperienceRole.objects.create(
                key=f"role_{i}",
                company=f"Company {i}",
                title=f"Title {i}",
            )
            roles.append(role)
            TemplateRoleConfig.objects.create(
                template=self.template,
                experience_role=role,
                order=i + 1,
                max_bullet_count=1,
            )
            ResumeExperienceBullet.objects.create(
                resume=self.resume,
                experience_role=role,
                order=1,
                text=f"Bullet {i}",
            )

        context = self.resume._build_template_context()

        self.assertIn("first_role_bullets", context)
        self.assertIn("sixth_role_bullets", context)
        self.assertIn("role_7_bullets", context)

    def test_render_to_pdf_creates_output_directory(self) -> None:
        """Test that render_to_pdf creates output directory if it doesn't exist."""
        mock_path_instance = MagicMock()
        self.mock_path.return_value = mock_path_instance
        self.mock_render.return_value = "<html></html>"
        
        mock_html_instance = MagicMock()
        self.mock_html.return_value = mock_html_instance

        self.resume.render_to_pdf(output_dir=self.OUTPUT_DIR)

        self.mock_path.assert_called_once_with(self.OUTPUT_DIR)
        mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_render_to_pdf_calls_weasyprint_with_html_string(self) -> None:
        """Test that render_to_pdf passes HTML string to WeasyPrint."""
        mock_path_instance = MagicMock()
        self.mock_path.return_value = mock_path_instance
        
        html_content = "<html><body>Test Resume</body></html>"
        self.mock_render.return_value = html_content
        
        mock_html_instance = MagicMock()
        self.mock_html.return_value = mock_html_instance

        self.resume.render_to_pdf(output_dir=self.OUTPUT_DIR)

        self.mock_html.assert_called_once_with(string=html_content)
        mock_html_instance.write_pdf.assert_called_once()

    def test_render_to_pdf_returns_correct_path(self) -> None:
        """Test that render_to_pdf returns correct PDF path."""
        mock_path_instance = MagicMock()
        self.mock_path.return_value = mock_path_instance
        mock_path_instance.__truediv__ = lambda self, other: Path(self.OUTPUT_DIR) / other
        
        self.mock_render.return_value = "<html></html>"
        mock_html_instance = MagicMock()
        self.mock_html.return_value = mock_html_instance

        result = self.resume.render_to_pdf(output_dir=self.OUTPUT_DIR)

        expected_filename = "Meta_Software_Engineer.pdf"
        self.assertTrue(result.endswith(expected_filename))

    def test_render_to_pdf_uses_default_output_directory(self) -> None:
        """Test that render_to_pdf uses default output directory."""
        mock_path_instance = MagicMock()
        self.mock_path.return_value = mock_path_instance
        self.mock_render.return_value = "<html></html>"
        mock_html_instance = MagicMock()
        self.mock_html.return_value = mock_html_instance

        self.resume.render_to_pdf()

        self.mock_path.assert_called_once_with("output/resumes")
