"""
Integration tests for resume PDF generation.

These tests are skipped by default since PDFs only need regeneration when templates/styles change.
To run them, temporarily comment out the @pytest.mark.skip decorator on the class.

PDFs are saved to resume/tests/test_output/
"""
import pytest
from datetime import datetime
from freezegun import freeze_time
from pathlib import Path

from django.test import TestCase
from django.utils import timezone

from resume.models import (
    ExperienceRole,
    Resume,
    ResumeRole,
    ResumeRoleBullet,
    ResumeSkillsCategory,
    ResumeTemplate,
    StylePath,
    TemplatePath,
)
from tracker.models import Job


@pytest.mark.skip(reason="Run manually when templates/styles change")
@freeze_time(timezone.make_aware(datetime(2024, 5, 11), timezone.get_current_timezone()))
class TestResumeModelIntegration(TestCase):
    
    OUTPUT_DIR = "resume/tests/test_output"

    NAVIT_KEY = "navit"
    AMAZON_SDE_KEY = "amazon_sde"
    AMAZON_BIE_KEY = "amazon_bie"
    AVENU_KEY = "avenu" 

    BULLETS = {
        NAVIT_KEY: [
            "Built REST API endpoints with Django REST Framework for financial goal tracking, implementing filtering, date range queries, and serializers that calculate statistics across monthly periods",
            "Developed Python REST API clients with pagination and rate limit handling for Smartlook and Intercom platform integrations, implementing incremental sync logic and automated retry mechanisms",
            "Configured monitoring and notifications using Slack API integration for sync status reporting, deletion summaries, and error tracking across backend services",
            "Implemented CI/CD automation with Celery and django-celery-beat for scheduled tasks including weekly session syncs, user cleanup jobs, and automated notification delivery with Firebase Cloud Messaging",
        ],
        AMAZON_SDE_KEY: [
            "Built RESTful APIs using Java on AWS to support global Prime Rewards promotion tracking, handling billions of requests with low latency across multiple regions",
            "Developed event-driven serverless workflows using AWS Lambda and DynamoDB, implementing stateless token-based promotion flows with fault-tolerant reward delivery logic",
            "Created full-stack admin portal with Vue.js and Java backend, enabling non-technical stakeholders to manage promotions and configurations through CRUD operations on DynamoDB",
            "Collaborated with cross-functional teams using Git for version control, participated in code reviews and sprint planning to deliver scalable features on schedule",
        ],
        AMAZON_BIE_KEY: [
            "Delivered on-time executive dashboards for Amazon Transportation Services by optimizing SQL queries and data pipelines, reducing query execution time by 30% to meet early-morning SLAs.",
            "Built scalable data pipelines using Amazon S3, Glue, and Redshift, reducing third-party vendor onboarding time and enabling operational growth through standardized SOPs.",
        ],
        AVENU_KEY: [
            "Saved 5+ hours weekly by developing a desktop GUI application using Python (tkinter) and SQL to automate PDF report generation.",
            "Improved large-scale data processing efficiency by applying Python chunking techniques to handle datasets exceeding 20M records.",
        ],
    }

    SKILLS = [
        ("Languages", "Python, Java, JavaScript, SQL, HTML, CSS"),
        ("Frameworks", "Django, React"),
        ("Databases", "PostgreSQL, DynamoDB"),
        ("Cloud & DevOps", "AWS, GCP, Docker"),
    ]
    
    @classmethod
    def setUpTestData(cls):
        cls.output_dir = Path(cls.OUTPUT_DIR)
        cls.output_dir.mkdir(parents=True, exist_ok=True)

        cls.navit_role = ExperienceRole.objects.create(
            key=cls.NAVIT_KEY,
            company="Nav.it",
            title="Software Engineer",
            start_date=timezone.datetime(2023, 5, 15),
            end_date=timezone.datetime(2024, 5, 31),
            location="Remote",
        )
        cls.amazon_sde_role = ExperienceRole.objects.create(
            key=cls.AMAZON_SDE_KEY,
            company="Amazon.com",
            title="Software Development Engineer",
            start_date=timezone.datetime(2022, 1, 31),
            end_date=timezone.datetime(2023, 3, 31),
            location="Seattle, WA",
        )
        cls.amazon_bie_role = ExperienceRole.objects.create(
            key=cls.AMAZON_BIE_KEY,
            company="Amazon.com",
            title="Business Intelligence Engineer II",
            start_date=timezone.datetime(2020, 8, 24),
            end_date=timezone.datetime(2022, 1, 14),
            location="Seattle, WA",
        )
        cls.avenu_role = ExperienceRole.objects.create(
            key=cls.AVENU_KEY,
            company="Avenu Insight & Analytics",
            title="Business Analyst",
            start_date=timezone.datetime(2016, 7, 1),
            end_date=timezone.datetime(2019, 5, 31),
            location="Fresno, CA",
        )

    def test_render_to_pdf_with_engineer_template_and_standard_style(self):
        template = ResumeTemplate.objects.create(template_path=TemplatePath.ENGINEER)
        job = Job.objects.create(company="Engineer Standard")
        resume = self._create_resume(template, job, StylePath.STANDARD)
        self._create_resume_role_and_bullets(resume, self.navit_role, order=1, bullets_key=self.NAVIT_KEY)
        self._create_resume_role_and_bullets(
            resume, self.amazon_sde_role, order=2, bullets_key=self.AMAZON_SDE_KEY, bullet_count_limit=3
        )
        self._create_skills(resume)

        pdf_path = resume.render_to_pdf(self.OUTPUT_DIR)
        
        self.assertTrue(Path(pdf_path).exists())

    def test_render_to_pdf_with_engineer_template_and_compact_style(self):
        template = ResumeTemplate.objects.create(template_path=TemplatePath.ENGINEER)
        job = Job.objects.create(company="Engineer Compact")
        resume = self._create_resume(template, job, StylePath.COMPACT)
        self._create_resume_role_and_bullets(resume, self.navit_role, order=1, bullets_key=self.NAVIT_KEY)
        self._create_resume_role_and_bullets(
            resume, self.amazon_sde_role, order=2, bullets_key=self.AMAZON_SDE_KEY, bullet_count_limit=3
        )
        self._create_resume_role_and_bullets(
            resume, self.avenu_role, order=3, bullets_key=self.AVENU_KEY, title_override="Software Developer"
        )
        self._create_skills(resume)

        pdf_path = resume.render_to_pdf(self.OUTPUT_DIR)
        
        self.assertTrue(Path(pdf_path).exists())

    def test_render_to_pdf_with_engineer_template_and_dense_style(self):
        template = ResumeTemplate.objects.create(template_path=TemplatePath.ENGINEER)
        job = Job.objects.create(company="Engineer Dense")
        resume = self._create_resume(template, job, StylePath.DENSE)
        self._create_resume_role_and_bullets(resume, self.navit_role, order=1, bullets_key=self.NAVIT_KEY)
        self._create_resume_role_and_bullets(resume, self.amazon_sde_role, order=2, bullets_key=self.AMAZON_SDE_KEY)
        self._create_resume_role_and_bullets(resume, self.amazon_bie_role, order=3, bullets_key=self.AMAZON_BIE_KEY)
        self._create_resume_role_and_bullets(resume, self.avenu_role, order=4, bullets_key=self.AVENU_KEY)
        self._create_skills(resume)

        pdf_path = resume.render_to_pdf(self.OUTPUT_DIR)
        
        self.assertTrue(Path(pdf_path).exists())

    def test_render_to_pdf_with_analyst_template_and_standard_style(self):
        template = ResumeTemplate.objects.create(template_path=TemplatePath.ANALYST)
        job = Job.objects.create(company="Analyst Standard")
        resume = self._create_resume(template, job, StylePath.STANDARD)
        self._create_resume_role_and_bullets(resume, self.navit_role, order=1, bullets_key=self.NAVIT_KEY)
        self._create_resume_role_and_bullets(
            resume, self.amazon_sde_role, order=2, bullets_key=self.AMAZON_SDE_KEY, bullet_count_limit=3
        )
        self._create_skills(resume)

        pdf_path = resume.render_to_pdf(self.OUTPUT_DIR)
        
        self.assertTrue(Path(pdf_path).exists())

    def test_render_to_pdf_with_analyst_template_and_compact_style(self):
        template = ResumeTemplate.objects.create(template_path=TemplatePath.ANALYST)
        job = Job.objects.create(company="Analyst Compact")
        resume = self._create_resume(template, job, StylePath.COMPACT)
        self._create_resume_role_and_bullets(resume, self.navit_role, order=1, bullets_key=self.NAVIT_KEY)
        self._create_resume_role_and_bullets(resume, self.amazon_sde_role, order=2, bullets_key=self.AMAZON_SDE_KEY)
        self._create_resume_role_and_bullets(resume, self.amazon_bie_role, order=3, bullets_key=self.AMAZON_BIE_KEY)
        self._create_skills(resume)

        pdf_path = resume.render_to_pdf(self.OUTPUT_DIR)
        
        self.assertTrue(Path(pdf_path).exists())

    def test_render_to_pdf_with_analyst_template_and_dense_style(self):
        template = ResumeTemplate.objects.create(template_path=TemplatePath.ANALYST)
        job = Job.objects.create(company="Analyst Dense")
        resume = self._create_resume(template, job, StylePath.DENSE)
        self._create_resume_role_and_bullets(resume, self.navit_role, order=1, bullets_key=self.NAVIT_KEY)
        self._create_resume_role_and_bullets(resume, self.amazon_sde_role, order=2, bullets_key=self.AMAZON_SDE_KEY)
        self._create_resume_role_and_bullets(resume, self.amazon_bie_role, order=3, bullets_key=self.AMAZON_BIE_KEY)
        self._create_resume_role_and_bullets(resume, self.avenu_role, order=4, bullets_key=self.AVENU_KEY)
        self._create_skills(resume)

        pdf_path = resume.render_to_pdf(self.OUTPUT_DIR)
        
        self.assertTrue(Path(pdf_path).exists())

    def _create_resume(self, template, job, style_path):
        resume = Resume.objects.create(template=template, job=job, style_path=style_path)
        return resume

    def _create_resume_role_and_bullets(
            self, resume, experience_role, order, bullets_key, bullet_count_limit = None, title_override = None
            ):
        title = title_override if title_override else experience_role.title
        role = ResumeRole.objects.create(
            resume=resume,
            source_role=experience_role,
            title=title,
            order=order,
        )
        bullets = self.BULLETS[bullets_key][:bullet_count_limit] if bullet_count_limit else self.BULLETS[bullets_key]
        for i, bullet in enumerate(bullets, start=1):
            ResumeRoleBullet.objects.create(
                resume_role=role,
                order=i,
                text=bullet,
            )

    def _create_skills(self, resume):
        for i, (cat, text) in enumerate(self.SKILLS, start=1):
            ResumeSkillsCategory.objects.create(resume=resume, order=i, category=cat, skills_text=text)
