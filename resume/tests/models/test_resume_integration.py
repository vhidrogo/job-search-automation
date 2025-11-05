"""
Integration tests for resume PDF generation.

These tests are skipped by default since PDFs only need regeneration when templates/styles change.
To run them, temporarily comment out the @pytest.mark.skip decorator on the class.

PDFs are saved to resume/tests/test_output/
"""
import pytest
from pathlib import Path

from django.test import TestCase

from resume.models import (
    ExperienceRole,
    Resume,
    ResumeExperienceBullet,
    ResumeSkillBullet,
    ResumeTemplate,
    TemplateRoleConfig,
)
from tracker.models import Job, JobLevel, JobRole, WorkSetting


@pytest.mark.skip(reason="Run manually when templates/styles change")
class TestResumeModelIntegration(TestCase):
    
    OUTPUT_DIR = "resume/tests/test_output"

    NAVIT_KEY = "navit"
    AMAZON_SDE_KEY = "amazon_sde"

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
        )

        cls.amazon_sde_role = ExperienceRole.objects.create(
            key=cls.AMAZON_SDE_KEY,
            company="Amazon.com",
            title="Software Development Engineer",
        )

    def test_render_to_pdf_software_engineer_i(self):
        target_role, target_level = JobRole.SOFTWARE_ENGINEER, JobLevel.I
        
        template = ResumeTemplate.objects.create(
            target_role=target_level,
            target_level=target_role,
            template_path="html/software_engineer_i.html",
            style_path="css/resume_standard.css",
        )

        job = self._create_job(target_role, target_level)
        resume = self._create_resume(template, job)
       
        navit_bullet_count = 4
        TemplateRoleConfig.objects.create(
            template=template,
            experience_role=self.navit_role,
            order=1,
            max_bullet_count=navit_bullet_count,
        )
        self._create_experience_bullets(resume, self.navit_role, navit_bullet_count, self.NAVIT_KEY)

        amazon_sde_bullet_count = 4
        TemplateRoleConfig.objects.create(
            template=template,
            experience_role=self.amazon_sde_role,
            order=2,
            max_bullet_count=amazon_sde_bullet_count,
        )
        self._create_experience_bullets(resume, self.amazon_sde_role, amazon_sde_bullet_count, self.AMAZON_SDE_KEY)

        self._create_skills(resume)

        pdf_path = resume.render_to_pdf(self.OUTPUT_DIR)
        
        self.assertTrue(Path(pdf_path).exists())

    def _create_job(self, target_role, target_level):
        job = Job.objects.create(
            company="Meta",
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

    def _create_experience_bullets(self, resume, experience_role, bullet_count, bullets_key):
        for i in range(bullet_count):
            ResumeExperienceBullet.objects.create(
                resume=resume,
                experience_role=experience_role,
                order=i + 1,
                text=self.BULLETS[bullets_key][i],
            )

    def _create_skills(self, resume):
        for cat, text in self.SKILLS:
            ResumeSkillBullet.objects.create(resume=resume, category=cat, skills_text=text)
