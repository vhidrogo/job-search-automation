"""
Integration tests for resume PDF generation.

These tests are skipped by default since PDFs only need regeneration when templates/styles change.
To run them, temporarily comment out the @pytest.mark.skip decorator on the class.

PDFs are saved to resume/tests/test_output/
"""
import pytest
from pathlib import Path

from django.test import TestCase
from django.utils import timezone

from resume.models import (
    ExperienceRole,
    Resume,
    ResumeExperienceBullet,
    ResumeSkillBullet,
    ResumeTemplate,
    StylePath,
    TemplatePath,
    TemplateRoleConfig,
)
from tracker.models import Job, JobLevel, JobRole, WorkSetting


@pytest.mark.skip(reason="Run manually when templates/styles change")
class TestResumeModelIntegration(TestCase):
    
    OUTPUT_DIR = "resume/tests/test_output"

    NAVIT_KEY = "navit"
    AMAZON_SDE_KEY = "amazon_sde"
    AMAZON_BIE_KEY = "amazon_bie"
    AVENU_KEY = "avenu" 

    BULLETS = {
        NAVIT_KEY: [
            "Built REST API endpoints with Django REST Framework for financial goal tracking, implementing filtering, date range queries, and serializers that calculate spending statistics across weekly and monthly periods",
            "Developed Python REST API clients with pagination and rate limit handling for Smartlook and Intercom platform integrations, implementing incremental sync logic and automated retry mechanisms",
            "Configured monitoring and notifications using Slack API integration for sync status reporting, deletion summaries, and error tracking across backend services",
            "Implemented CI/CD automation with Celery and django-celery-beat for scheduled tasks including weekly session syncs, user cleanup jobs, and automated notification delivery with Firebase Cloud Messaging",
        ],
        AMAZON_SDE_KEY: [
            "Built RESTful APIs and microservices in Java on AWS to support global Prime Rewards promotion tracking, handling billions of requests with low latency across multiple regions",
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
        target_role, target_level = JobRole.SOFTWARE_ENGINEER, JobLevel.I
        template = ResumeTemplate.objects.create(
            target_role=target_level,
            target_level=target_role,
            template_path=TemplatePath.ENGINEER,
            style_path=StylePath.STANDARD,
        )
        job = self._create_job("Engineer Standard", target_role, target_level)
        resume = self._create_resume(template, job)
        self._create_config(template, self.navit_role, order=1)
        self._create_config(template, self.amazon_sde_role, order=2)
        self._create_experience_bullets(resume, self.navit_role, self.NAVIT_KEY)
        self._create_experience_bullets(resume, self.amazon_sde_role, self.AMAZON_SDE_KEY)
        self._create_skills(resume)

        pdf_path = resume.render_to_pdf(self.OUTPUT_DIR)
        
        self.assertTrue(Path(pdf_path).exists())

    def test_render_to_pdf_with_engineer_template_and_compact_style(self):
        target_role, target_level = JobRole.SOFTWARE_ENGINEER, JobLevel.II
        template = ResumeTemplate.objects.create(
            target_role=target_level,
            target_level=target_role,
            template_path=TemplatePath.ENGINEER,
            style_path=StylePath.COMPACT,
        )
        job = self._create_job("Engineer Compact", target_role, target_level)
        resume = self._create_resume(template, job)
        self._create_config(template, self.navit_role, order=1)
        self._create_config(template, self.amazon_sde_role, order=2)
        self._create_config(template, self.avenu_role, order=3, title_override="Software Developer")
        self._create_experience_bullets(resume, self.navit_role, self.NAVIT_KEY)
        self._create_experience_bullets(resume, self.amazon_sde_role, self.AMAZON_SDE_KEY)
        self._create_experience_bullets(resume, self.avenu_role, self.AVENU_KEY)
        self._create_skills(resume)

        pdf_path = resume.render_to_pdf(self.OUTPUT_DIR)
        
        self.assertTrue(Path(pdf_path).exists())

    def test_render_to_pdf_with_engineer_template_and_dense_style(self):
        target_role, target_level = JobRole.SOFTWARE_ENGINEER, JobLevel.II
        template = ResumeTemplate.objects.create(
            target_role=target_level,
            target_level=target_role,
            template_path=TemplatePath.ENGINEER,
            style_path=StylePath.DENSE,
        )
        job = self._create_job("Engineer Dense", target_role, target_level)
        resume = self._create_resume(template, job)
        self._create_config(template, self.navit_role, order=1)
        self._create_config(template, self.amazon_sde_role, order=2)
        self._create_config(template, self.amazon_bie_role, order=3)
        self._create_config(template, self.avenu_role, order=4)
        self._create_experience_bullets(resume, self.navit_role, self.NAVIT_KEY)
        self._create_experience_bullets(resume, self.amazon_sde_role, self.AMAZON_SDE_KEY)
        self._create_experience_bullets(resume, self.amazon_bie_role, self.AMAZON_BIE_KEY)
        self._create_experience_bullets(resume, self.avenu_role, self.AVENU_KEY)
        self._create_skills(resume)

        pdf_path = resume.render_to_pdf(self.OUTPUT_DIR)
        
        self.assertTrue(Path(pdf_path).exists())

    def test_render_to_pdf_with_analyst_template_and_standard_style(self):
        target_role, target_level = JobRole.DATA_ANALYST, JobLevel.II
        template = ResumeTemplate.objects.create(
            target_role=target_level,
            target_level=target_role,
            template_path=TemplatePath.ANALYST,
            style_path=StylePath.STANDARD,
        )
        job = self._create_job("Analyst Standard", target_role, target_level)
        resume = self._create_resume(template, job)
        self._create_config(template, self.navit_role, order=1)
        self._create_config(template, self.amazon_sde_role, order=2)
        self._create_experience_bullets(resume, self.navit_role, self.NAVIT_KEY)
        self._create_experience_bullets(resume, self.amazon_sde_role, self.AMAZON_SDE_KEY)
        self._create_skills(resume)

        pdf_path = resume.render_to_pdf(self.OUTPUT_DIR)
        
        self.assertTrue(Path(pdf_path).exists())

    def test_render_to_pdf_with_analyst_template_and_compact_style(self):
        target_role, target_level = JobRole.DATA_ANALYST, JobLevel.SENIOR
        template = ResumeTemplate.objects.create(
            target_role=target_level,
            target_level=target_role,
            template_path=TemplatePath.ANALYST,
            style_path=StylePath.COMPACT,
        )
        job = self._create_job("Analyst Compact", target_role, target_level)
        resume = self._create_resume(template, job)
        self._create_config(template, self.navit_role, order=1)
        self._create_config(template, self.amazon_sde_role, order=2)
        self._create_config(template, self.amazon_bie_role, order=3)
        self._create_experience_bullets(resume, self.navit_role, self.NAVIT_KEY)
        self._create_experience_bullets(resume, self.amazon_sde_role, self.AMAZON_SDE_KEY)
        self._create_experience_bullets(resume, self.amazon_bie_role, self.AMAZON_BIE_KEY)
        self._create_skills(resume)

        pdf_path = resume.render_to_pdf(self.OUTPUT_DIR)
        
        self.assertTrue(Path(pdf_path).exists())

    def test_render_to_pdf_with_analyst_template_and_dense_style(self):
        target_role, target_level = JobRole.DATA_ANALYST, JobLevel.SENIOR
        template = ResumeTemplate.objects.create(
            target_role=target_level,
            target_level=target_role,
            template_path=TemplatePath.ANALYST,
            style_path=StylePath.DENSE,
        )
        job = self._create_job("Analyst Dense", target_role, target_level)
        resume = self._create_resume(template, job)
        self._create_config(template, self.navit_role, order=1)
        self._create_config(template, self.amazon_sde_role, order=2)
        self._create_config(template, self.amazon_bie_role, order=3)
        self._create_config(template, self.avenu_role, order=4)
        self._create_experience_bullets(resume, self.navit_role, self.NAVIT_KEY)
        self._create_experience_bullets(resume, self.amazon_sde_role, self.AMAZON_SDE_KEY)
        self._create_experience_bullets(resume, self.amazon_bie_role, self.AMAZON_BIE_KEY)
        self._create_experience_bullets(resume, self.avenu_role, self.AVENU_KEY)
        self._create_skills(resume)

        pdf_path = resume.render_to_pdf(self.OUTPUT_DIR)
        
        self.assertTrue(Path(pdf_path).exists())

    def _create_job(self, company, target_role, target_level):
        job = Job.objects.create(
            company=company,
            listing_job_title=target_role,
            role=target_role,
            level=target_level,
            location="Seattle, WA",
            work_setting=WorkSetting.HYBRID,
        )

        return job

    def _create_resume(self, template, job):
        resume = Resume.objects.create(template=template, job=job)
        return resume
    
    def _create_config(self, template, role, order, title_override = None):
        TemplateRoleConfig.objects.create(
            template=template,
            experience_role=role,
            title_override=title_override,
            order=order,
            max_bullet_count=1,
        )

    def _create_experience_bullets(self, resume, experience_role, bullets_key):
        for i, bullet in enumerate(self.BULLETS[bullets_key], start=1):
            ResumeExperienceBullet.objects.create(
                resume=resume,
                experience_role=experience_role,
                order=i,
                text=bullet,
            )

    def _create_skills(self, resume):
        for cat, text in self.SKILLS:
            ResumeSkillBullet.objects.create(resume=resume, category=cat, skills_text=text)
