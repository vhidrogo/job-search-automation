from pathlib import Path
from unittest.mock import ANY, patch
from weasyprint import HTML

from django.test import TestCase
from django.utils import timezone

from resume.models import (
    ExperienceRole,
    Resume,
    ResumeExperienceBullet,
    ResumeSkillBullet,
    ResumeTemplate,
    TemplateRoleConfig,
)
from tracker.models import Job, JobRole, JobLevel


class TestResumeModel(TestCase):
    ROLE1_COMPANY = "Nav.it"
    ROLE1_TITLE = "Software Engineer"
    ROLE1_LOCATION = "Remote"
    ROLE2_COMPANY = "Amazon.com"
    ROLE2_TITLE = "Software Development Engineer"
    ROLE2_LOCATION = "Seattle, WA"
    TEMPLATE_PATH = "template/path"

    @classmethod
    def setUpTestData(self):
        self.template = ResumeTemplate.objects.create(
            template_path=self.TEMPLATE_PATH,
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
        )
        job = Job.objects.create(
            company="Meta",
            listing_job_title="Software Engineer",
            level=JobLevel.II,
        )
        self.resume = Resume.objects.create(
            job=job,
            template=self.template,
        )
        self.role1 = ExperienceRole.objects.create(
            key="role1",
            company=self.ROLE1_COMPANY,
            title=self.ROLE1_TITLE,
            start_date=timezone.datetime(2023, 5, 15),
            end_date=timezone.datetime(2024, 5, 31),
            location=self.ROLE1_LOCATION,
        )
        self.role2 = ExperienceRole.objects.create(
            key="role2",
            company=self.ROLE2_COMPANY,
            title=self.ROLE2_TITLE,
            start_date=timezone.datetime(2022, 1, 31),
            end_date=timezone.datetime(2023, 3, 31),
            location=self.ROLE2_LOCATION,
        )

    def _create_default_config(self, role, order):
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=role,
            order=order,
            max_bullet_count=1,
        )

    def _get_context(self, context_var):
        self.mock_render.assert_called_once_with(ANY, ANY)
        context = self.mock_render.call_args[0][1]
        self.assertIn(context_var, context)
        
        return context[context_var]

    def setUp(self):
        mkdir_patcher = patch.object(Path, "mkdir")
        self.mock_mkdir = mkdir_patcher.start()
        self.addCleanup(mkdir_patcher.stop)
        
        render_patcher = patch("resume.models.resume.render_to_string")
        self.mock_render = render_patcher.start()
        self.addCleanup(self.mock_render.stop)
        self.mock_render.return_value = "<html><body>Resume Content</body></html>"

        write_patcher = patch.object(HTML, "write_pdf")
        self.mock_write = write_patcher.start()
        self.addCleanup(write_patcher.stop)

        css_patcher = patch("resume.models.resume.CSS")
        self.mock_css = css_patcher.start()
        self.addCleanup(css_patcher.stop)

    def test_render_to_pdf_uses_template_and_default_output_dir(self):
        result = self.resume.render_to_pdf()

        self.mock_mkdir.assert_called_once()
        self.mock_render.assert_called_once_with(self.TEMPLATE_PATH, ANY)
        self.mock_write.assert_called_once()
        self.mock_css.assert_called_once()
        self.assertEqual(result, f"output/resumes/Meta_Software_Engineer_II.pdf")

    def test_render_to_pdf_renders_one_experience_entry_per_config_role_in_order(self):
        self._create_default_config(self.role1, order=1)
        self._create_default_config(self.role2, order=2)

        self.resume.render_to_pdf()

        experience_html = self._get_context("experience")
        expected_role_count = 2
        self.assertEqual(experience_html.count('class="experience-entry"'), expected_role_count)
        self.assertEqual(experience_html.count('class="experience-header"'), expected_role_count)
        self.assertEqual(experience_html.count('class="experience-title"'), expected_role_count)
        self.assertEqual(experience_html.count('class="experience-dates"'), expected_role_count)
        self.assertEqual(experience_html.count('class="experience-subheader"'), expected_role_count)
        self.assertEqual(experience_html.count('class="experience-company"'), expected_role_count)
        self.assertEqual(experience_html.count('class="experience-location"'), expected_role_count)
        self.assertEqual(experience_html.count('class="experience-bullets"'), expected_role_count)
        self.assertIn(self.ROLE1_COMPANY, experience_html)
        self.assertIn(self.ROLE2_COMPANY, experience_html)
        self.assertLess(experience_html.index(self.ROLE1_COMPANY), experience_html.index(self.ROLE2_COMPANY))
        self.assertIn(self.ROLE1_TITLE, experience_html)
        self.assertIn(self.ROLE2_TITLE, experience_html)
        self.assertLess(experience_html.index(self.ROLE1_TITLE), experience_html.index(self.ROLE2_TITLE))
        self.assertIn(self.ROLE1_LOCATION, experience_html)
        self.assertIn(self.ROLE2_LOCATION, experience_html)
        self.assertLess(experience_html.index(self.ROLE1_LOCATION), experience_html.index(self.ROLE2_LOCATION))
        expected_role1_dates, expected_role2_dates = "May 2023 - May 2024", "Jan 2022 - Mar 2023"
        self.assertIn(expected_role1_dates, experience_html)
        self.assertIn(expected_role2_dates, experience_html)
        self.assertLess(experience_html.index(expected_role1_dates), experience_html.index(expected_role2_dates))

    def test_render_to_pdf_use_title_override_when_present(self):
        title_override = "Software Engineer (Backend)"
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role1,
            title_override=title_override,
            order=1,
            max_bullet_count=1,
        )

        self.resume.render_to_pdf()

        experience_html = self._get_context("experience")
        self.assertIn(title_override, experience_html)

    def test_render_to_pdf_per_renders_bullets_in_order(self):
        self._create_default_config(self.role1, order=1)
        bullet1_text = "Built REST API endpoints for goal tracking with Django REST Framework"
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role1,
            order=1,
            text=bullet1_text,
        )
        bullet2_text = "Developed API clients for Smartlook and Intercom integrations"
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role1,
            order=2,
            text=bullet2_text,
        )

        self.resume.render_to_pdf()

        experience_html = self._get_context("experience")
        self.assertIn(bullet1_text, experience_html)
        self.assertIn(bullet2_text, experience_html)
        self.assertLess(experience_html.index(bullet1_text), experience_html.index(bullet2_text))
        self.assertIn('<ul', experience_html)
        self.assertIn('<li>', experience_html)

    def test_render_to_pdf_uses_bullet_override_text_when_present(self):
        self._create_default_config(self.role1, order=1)
        text = "Built REST API endpoints for goal tracking with Django REST Framework"
        override_text = "Developed API clients for Smartlook and Intercom integrations"
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role1,
            order=1,
            text=text,
            override_text=override_text,
        )

        self.resume.render_to_pdf()

        experience_html = self._get_context("experience")
        self.assertIn(override_text, experience_html)
        self.assertNotIn(text, experience_html)

    def test_render_to_pdf_does_not_render_excluded_bullets(self):
        self._create_default_config(self.role1, order=1)
        text = "Built REST API endpoints for goal tracking with Django REST Framework"
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role1,
            order=1,
            text=text,
            exclude=True,
        )

        self.resume.render_to_pdf()

        experience_html = self._get_context("experience")
        self.assertNotIn(text, experience_html)

    def test_render_to_pdf_renders_skills(self):
        category1, skills1 = "Programming Languages", "Python, Java"
        ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=category1,
            skills_text=skills1,
        )
        category2, skills2 = "Frameworks", "Django, React"
        ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=category2,
            skills_text=skills2,
        )

        self.resume.render_to_pdf()
        
        skills_html = self._get_context("skills")
        self.assertIn(category1, skills_html)
        self.assertIn(skills1, skills_html)
        self.assertIn(category2, skills_html)
        self.assertIn(skills2, skills_html)
        self.assertIn('class="skill-category"', skills_html)
        self.assertIn('<strong>', skills_html)

    def test_str(self):
        self.assertEqual(str(self.resume), "Resume for Meta - Software Engineer")
  