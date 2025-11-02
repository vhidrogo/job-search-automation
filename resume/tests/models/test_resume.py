from django.test import TestCase
from pathlib import Path
from unittest.mock import ANY, patch
from weasyprint import HTML

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
    COMPANY = "Meta"
    LISTING_JOB_TITLE = "Software Engineer"
    MOCK_HTML_CONTENT = "<html><body>Resume Content</body></html>"
    TEMPLATE_PATH = "template/path"

    @classmethod
    def setUpTestData(self):
        self.template = ResumeTemplate.objects.create(
            template_path=self.TEMPLATE_PATH,
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
            )
        job = Job.objects.create(
            company=self.COMPANY,
            listing_job_title=self.LISTING_JOB_TITLE,
        )
        self.resume = Resume.objects.create(
            job=job,
            template=self.template,
            )
        self.role = ExperienceRole.objects.create(key="key1")

    def test_str(self):
        self.assertEqual(str(self.resume), "Resume for Meta - Software Engineer")

    @patch("resume.models.resume.CSS")
    @patch.object(HTML, "write_pdf")
    @patch.object(Path, "mkdir")
    @patch("resume.models.resume.render_to_string")
    def test_render_to_pdf_calls_dependencies_and_returns_path(self, mock_render, mock_mkdir, mock_write, mock_css):
        mock_render.return_value = self.MOCK_HTML_CONTENT

        result = self.resume.render_to_pdf()

        mock_mkdir.assert_called_once()
        mock_render.assert_called_once_with(self.TEMPLATE_PATH, ANY)
        self.assertEqual(result, "output/resumes/Meta_Software_Engineer.pdf")

    @patch("resume.models.resume.CSS")
    @patch.object(HTML, "write_pdf")
    @patch.object(Path, "mkdir")
    @patch("resume.models.resume.render_to_string")
    def test_render_to_pdf_sanitizes_file_name(self, mock_render, mock_mkdir, mock_write, mock_css):
        job = Job.objects.create(
            company="Has space",
            listing_job_title="#special chars!"
        )
        resume = Resume.objects.create(
            job=job,
            template=self.template
        )
        mock_render.return_value = self.MOCK_HTML_CONTENT

        result = resume.render_to_pdf()

        self.assertEqual(result, "output/resumes/Has_space_special_chars.pdf")

    @patch("resume.models.resume.CSS")
    @patch.object(HTML, "write_pdf")
    @patch.object(Path, "mkdir")
    @patch("resume.models.resume.render_to_string")
    def test_render_to_pdf_renders_role_using_bullet_order(self, mock_render, mock_mkdir, mock_write, mock_css):
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=1,
            max_bullet_count=1,
        )
        bullet_text2 = "bullet order 2"
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role,
            order=2,
            text=bullet_text2,
        )
        bullet_text1 = "bullet order 1"
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role,
            order=1,
            text=bullet_text1,
        )
        mock_render.return_value = self.MOCK_HTML_CONTENT

        self.resume.render_to_pdf()
        
        expected_context = {
            "experience_bullets_1": f"<li>{bullet_text1}</li>\n <li>{bullet_text2}</li>",
            "skills": ""
        }
        mock_render.assert_called_once_with(self.TEMPLATE_PATH, expected_context)

    @patch("resume.models.resume.CSS")
    @patch.object(HTML, "write_pdf")
    @patch.object(Path, "mkdir")
    @patch("resume.models.resume.render_to_string")
    def test_render_to_pdf_renders_role_using_role_order(self, mock_render, mock_mkdir, mock_write, mock_css):
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=2,
            max_bullet_count=1,
        )
        bullet_text2 = "role 2 bullet"
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role,
            order=1,
            text=bullet_text2,
        )
        role = ExperienceRole.objects.create(key="other role")
        bullet_text1 = "role 1 bullet"
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=role,
            order=1,
            text=bullet_text1,
        )
        mock_render.return_value = self.MOCK_HTML_CONTENT

        self.resume.render_to_pdf()
        
        expected_context = {
            "experience_bullets_1": f"<li>{bullet_text1}</li>",
            "experience_bullets_1": f"<li>{bullet_text2}</li>",
            "skills": ""
        }
        mock_render.assert_called_once_with(self.TEMPLATE_PATH, expected_context)

    @patch("resume.models.resume.CSS")
    @patch.object(HTML, "write_pdf")
    @patch.object(Path, "mkdir")
    @patch("resume.models.resume.render_to_string")
    def test_render_to_pdf_renders_role_without_excluded(self, mock_render, mock_mkdir, mock_write, mock_css):
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=1,
            max_bullet_count=1,
        )
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role,
            order=2,
            text="excluded",
            exclude=True
        )
        mock_render.return_value = self.MOCK_HTML_CONTENT

        self.resume.render_to_pdf()
        
        expected_context = {
            "experience_bullets_1": "",
            "skills": ""
        }
        mock_render.assert_called_once_with(self.TEMPLATE_PATH, expected_context)

    @patch("resume.models.resume.CSS")
    @patch.object(HTML, "write_pdf")
    @patch.object(Path, "mkdir")
    @patch("resume.models.resume.render_to_string")
    def test_render_to_pdf_renders_role_using_override_text(self, mock_render, mock_mkdir, mock_write, mock_css):
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=1,
            max_bullet_count=1,
        )
        override_text = "overridden text"
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.role,
            order=2,
            text="text",
            override_text=override_text,
        )
        mock_render.return_value = self.MOCK_HTML_CONTENT

        self.resume.render_to_pdf()
        
        expected_context = {
            "experience_bullets_1": f"<li>{override_text}</li>",
            "skills": ""
        }
        mock_render.assert_called_once_with(self.TEMPLATE_PATH, expected_context)

    @patch("resume.models.resume.CSS")
    @patch.object(HTML, "write_pdf")
    @patch.object(Path, "mkdir")
    @patch("resume.models.resume.render_to_string")
    def test_render_to_pdf_renders_skills(self, mock_render, mock_mkdir, mock_write, mock_css):
        category1 = "category1"
        skills_text1 = "skills_text1"
        ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=category1,
            skills_text=skills_text1,
        )
        category2 = "category2"
        skills_text2 = "skills_text2"
        ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=category2,
            skills_text=skills_text2,
        )
        mock_render.return_value = self.MOCK_HTML_CONTENT

        self.resume.render_to_pdf()
        
        expected_context = {
            "skills": (
                f'<div class="skill-category"><strong>{category1}:</strong> {skills_text1}</div>\n'
                f'<div class="skill-category"><strong>{category2}:</strong> {skills_text2}</div>'
            )
        }
        mock_render.assert_called_once_with(self.TEMPLATE_PATH, expected_context)
    