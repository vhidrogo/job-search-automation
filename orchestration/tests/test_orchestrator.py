from unittest.mock import call, Mock, patch

from django.test import TestCase

from orchestration.orchestrator import Orchestrator
from resume.models import (
    ExperienceRole,
    Resume,
    ResumeExperienceBullet,
    ResumeTemplate,
    ResumeSkillBullet,
    TemplateRoleConfig,
)
from resume.schemas import (
    BulletListModel,
    ExperienceBullet,
    JDModel,
    Metadata,
    RequirementSchema,
    SkillCategorySchema,
    SkillBulletListModel,
)
from resume.services import JDParser, ResumeWriter
from tracker.models import (
    Job,
    JobLevel,
    JobRole,
    Requirement,
    WorkSetting,
)


class TestOrchestrator(TestCase):
    COMPANY = "Meta"
    JD_PATH = "test/jd_path"
    LISTING_JOB_TITLE = "Software Engineer"
    PDF_PATH = "test/pdf_path"
    REQUIREMENT_TEXT1 = "5+ years of Python experience"
    REQUIREMENT_TEXT2 = "Experience with Django web framework"
    SKILL_CATEGORY1 = "Programming Languages"
    SKILL_CATEGORY2 = "Frameworks"
    TARGET_LEVEL = JobLevel.II
    TARGET_ROLE = JobRole.SOFTWARE_ENGINEER

    @classmethod
    def setUpTestData(cls):
        cls.requirements = [
                RequirementSchema(
                    text=cls.REQUIREMENT_TEXT1,
                    keywords=["Python", "experience"],
                    relevance=0.95,
                ),
                RequirementSchema(
                    text=cls.REQUIREMENT_TEXT2,
                    keywords=["Django", "web framework"],
                    relevance=0.90,
                ),
            ]
        cls.jd_model = JDModel(
            metadata=Metadata(
                company=cls.COMPANY,
                listing_job_title=cls.LISTING_JOB_TITLE,
                role=cls.TARGET_ROLE,
                level=cls.TARGET_LEVEL,
                location="Seattle, WA",
                work_setting=WorkSetting.HYBRID,
            ),
            requirements=cls.requirements,
        )
        
        cls.skills = [
            SkillCategorySchema(
                category=cls.SKILL_CATEGORY1,
                skills="Python, Java",
            ),
            SkillCategorySchema(
                category=cls.SKILL_CATEGORY2,
                skills="Django, React",
            ),
        ]
        cls.skill_model = SkillBulletListModel(skill_categories=cls.skills)

        cls.mock_skill_model = Mock()
        cls.mock_skill_model.skill_categories = []

    def setUp(self):
        self.mock_jd_parser = Mock(spec=JDParser)
        self.mock_resume_writer = Mock(spec=ResumeWriter)

        self.mock_jd_parser.parse.return_value = self.jd_model
        self.mock_resume_writer.generate_skill_bullets.return_value = self.mock_skill_model

        self.orchestrator = Orchestrator(
            jd_parser=self.mock_jd_parser,
            resume_writer=self.mock_resume_writer,
        )

        patcher = patch("orchestration.orchestrator.Resume.render_to_pdf")
        self.mock_render_pdf = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_render_pdf.return_value = self.PDF_PATH

    def _create_default_template(self):
        self.template = ResumeTemplate.objects.create(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
        )

    def test_run_parses_jd_and_persists_job_requirements_and_resume(self):
        self._create_default_template()

        self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)

        # Verify Job was persisted
        self.mock_jd_parser.parse.assert_called_once_with(self.JD_PATH)
        self.assertEqual(Job.objects.count(), 1)
        job = Job.objects.first()
        self.assertEqual(job.company, self.COMPANY)
        self.assertEqual(job.listing_job_title, self.LISTING_JOB_TITLE)

        # Verify Requirements were persisted
        self.assertEqual(Requirement.objects.filter(job=job).count(), len(self.requirements))
        self.assertTrue(Requirement.objects.filter(job=job, text=self.REQUIREMENT_TEXT1).exists())
        self.assertTrue(Requirement.objects.filter(job=job, text=self.REQUIREMENT_TEXT2).exists())

        # Verify Resume was persisted
        self.assertEqual(Resume.objects.count(), 1)
        resume = Resume.objects.first()
        self.assertEqual(resume.template, self.template)
        self.assertEqual(resume.job, job)

    def test_run_raises_when_no_template(self):
        with self.assertRaises(ValueError) as cm:
            self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)

        error_msg = str(cm.exception)
        self.assertIn("No template found", error_msg)
        self.assertIn(self.TARGET_ROLE, error_msg)
        self.assertIn(self.TARGET_LEVEL, error_msg)

    def test_run_generates_and_persists_resume_bullets_for_all_roles(self):
        self._create_default_template()

        # Create test roles and configs
        max_bullet_count = 2
        role1 = ExperienceRole.objects.create(key="role1")
        role2 = ExperienceRole.objects.create(key="role2")
        for i, role in enumerate([role1, role2], start=1):
            TemplateRoleConfig.objects.create(
                template=self.template,
                experience_role=role,
                order=i,
                max_bullet_count=max_bullet_count,
            )

        # Create test bullet responses for each role
        role1_bullet1 = "Implemented REST APIs to improve data exchange between services."
        role1_bullet2 = "Optimized SQL queries, reducing request latency by 30%."
        bullet_list1 = [
            ExperienceBullet(order=1, text=role1_bullet1),
            ExperienceBullet(order=2, text=role1_bullet2),
        ]
        role2_bullet1 = "Developed unit tests to ensure code reliability and maintainability."
        role2_bullet2 = "Integrated third-party APIs to extend application functionality."
        bullet_list2 = [
            ExperienceBullet(order=1, text=role2_bullet1),
            ExperienceBullet(order=2, text=role2_bullet2),
        ]
        self.mock_resume_writer.generate_experience_bullets.side_effect = [
            BulletListModel(bullets=bullet_list1),
            BulletListModel(bullets=bullet_list2),
        ]

        self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)

        expected_calls = [
            call(
                experience_role=role,
                requirements=self.requirements,
                target_role=self.TARGET_ROLE,
                max_bullet_count=max_bullet_count,
            )
            for role in [role1, role2]
        ]
        self.mock_resume_writer.generate_experience_bullets.assert_has_calls(expected_calls)

        # Verify ResumeExperienceBullets for first role were persisted
        self.assertEqual(ResumeExperienceBullet.objects.filter(experience_role=role1).count(), len(bullet_list1))
        self.assertTrue(ResumeExperienceBullet.objects.filter(experience_role=role1, text=role1_bullet1).exists())
        self.assertTrue(ResumeExperienceBullet.objects.filter(experience_role=role1, text=role1_bullet2).exists())

        # Verify ResumeExperienceBullets for second role were persisted
        self.assertEqual(ResumeExperienceBullet.objects.filter(experience_role=role2).count(), len(bullet_list2))
        self.assertTrue(ResumeExperienceBullet.objects.filter(experience_role=role2, text=role2_bullet1).exists())
        self.assertTrue(ResumeExperienceBullet.objects.filter(experience_role=role2, text=role2_bullet2).exists())

    def test_run_generates_and_persists_resume_skills(self):
        self._create_default_template()
        self.mock_resume_writer.generate_skill_bullets.return_value = self.skill_model

        self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)

        self.mock_resume_writer.generate_skill_bullets.assert_called_once_with(self.template, self.requirements)
        self.assertEqual(ResumeSkillBullet.objects.count(), len(self.skills))
        self.assertTrue(ResumeSkillBullet.objects.filter(category=self.SKILL_CATEGORY1).exists())
        self.assertTrue(ResumeSkillBullet.objects.filter(category=self.SKILL_CATEGORY2).exists())
