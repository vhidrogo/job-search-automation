from unittest.mock import call, Mock, patch

from django.test import TestCase
from django.utils import timezone

from orchestration.orchestrator import Orchestrator
from resume.models import (
    ExperienceRole,
    Resume,
    ResumeRole,
    ResumeRoleBullet,
    ResumeTemplate,
    ResumeSkillsCategory,
    StylePath,
    TargetSpecialization,
    TemplateRoleConfig,
)
from resume.schemas import (
    BulletListModel,
    ExperienceBullet,
    JDModel,
    Metadata,
    RequirementSchema,
    SkillsCategorySchema,
    SkillsListModel,
)
from resume.services import JDParser, ResumeWriter
from tracker.models import (
    Application,
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
    SKILLS_CATEGORY1 = "Programming Languages"
    SKILLS_CATEGORY2 = "Frameworks"
    STYLE_PATH = "test/style_path"
    TARGET_LEVEL = JobLevel.II
    TARGET_ROLE = JobRole.SOFTWARE_ENGINEER
    TARGET_SPECIALIZATION = TargetSpecialization.BACKEND

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

        cls.jd_model_with_specialization = JDModel(
            metadata=Metadata(
                company=cls.COMPANY,
                listing_job_title=cls.LISTING_JOB_TITLE,
                role=cls.TARGET_ROLE,
                level=cls.TARGET_LEVEL,
                specialization=cls.TARGET_SPECIALIZATION,
                location="Seattle, WA",
                work_setting=WorkSetting.HYBRID,
            ),
            requirements=cls.requirements,
        )
        
        cls.skills = [
            SkillsCategorySchema(
                order=1,
                category=cls.SKILLS_CATEGORY1,
                skills="Python, Java",
            ),
            SkillsCategorySchema(
                order=2,
                category=cls.SKILLS_CATEGORY2,
                skills="Django, React",
            ),
        ]
        cls.skills_model = SkillsListModel(skills_categories=cls.skills)

        cls.mock_skills_model = Mock()
        cls.mock_skills_model.skills_categories = []

        cls.now = timezone.now()

    def setUp(self):
        self.mock_jd_parser = Mock(spec=JDParser)
        self.mock_resume_writer = Mock(spec=ResumeWriter)

        self.mock_jd_parser.parse.return_value = self.jd_model
        self.mock_resume_writer.generate_skills.return_value = self.mock_skills_model

        self.orchestrator = Orchestrator(
            jd_parser=self.mock_jd_parser,
            resume_writer=self.mock_resume_writer,
        )

        patcher = patch("orchestration.orchestrator.Resume.render_to_pdf")
        self.mock_render_pdf = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_render_pdf.return_value = self.PDF_PATH

        pdf_patcher = patch("orchestration.orchestrator.PdfReader")
        self.mock_pdf_reader = pdf_patcher.start()
        self.addCleanup(pdf_patcher.stop)

        self.mock_pdf_reader.return_value.pages = [object()]

    def _create_default_template(self):
        self.template = ResumeTemplate.objects.create(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            style_path=self.STYLE_PATH,
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
        self.assertEqual(resume.style_path, self.STYLE_PATH)

    def test_run_does_not_persist_when_no_template(self):
        with self.assertRaises(ValueError) as cm:
            self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)

        self.assertEqual(Job.objects.count(), 0)
        self.assertEqual(Resume.objects.count(), 0)
        self.assertEqual(ResumeRole.objects.count(), 0)
        self.assertEqual(ResumeRoleBullet.objects.count(), 0)
        self.assertEqual(ResumeSkillsCategory.objects.count(), 0)
        self.assertEqual(Application.objects.count(), 0)

    def test_run_raises_when_no_template_without_specialization(self):
        with self.assertRaises(ValueError) as cm:
            self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)

        error_msg = str(cm.exception)
        self.assertIn("No template found", error_msg)
        self.assertIn(self.TARGET_ROLE, error_msg)
        self.assertIn(self.TARGET_LEVEL, error_msg)

    def test_run_raises_when_no_template_with_specialization(self):
        self._create_default_template()
        self.mock_jd_parser.parse.return_value = self.jd_model_with_specialization
        
        with self.assertRaises(ValueError) as cm:
            self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)

        error_msg = str(cm.exception)
        self.assertIn("No template found", error_msg)
        self.assertIn(self.TARGET_ROLE, error_msg)
        self.assertIn(self.TARGET_LEVEL, error_msg)
        self.assertIn(self.TARGET_SPECIALIZATION, error_msg)

    def test_run_uses_template_for_target_specialization(self):
        template = ResumeTemplate.objects.create(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            target_specialization=self.TARGET_SPECIALIZATION,
            )
        self.mock_jd_parser.parse.return_value = self.jd_model_with_specialization

        self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)

        self.assertEqual(Resume.objects.count(), 1)
        resume = Resume.objects.first()
        self.assertEqual(resume.template, template)

    def test_run_uses_template_for_normalized_target_specialization(self):
        template = ResumeTemplate.objects.create(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            target_specialization=TargetSpecialization.FULL_STACK,
            )
        self.mock_jd_parser.parse.return_value = JDModel(
            metadata=Metadata(
                company=self.COMPANY,
                listing_job_title=self.LISTING_JOB_TITLE,
                role=self.TARGET_ROLE,
                level=self.TARGET_LEVEL,
                specialization="full -Stack",
                location="Seattle, WA",
                work_setting=WorkSetting.HYBRID,
            ),
            requirements=self.requirements,
        )

        self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)

        self.assertEqual(Resume.objects.count(), 1)
        resume = Resume.objects.first()
        self.assertEqual(resume.template, template)

    def test_run_uses_role_and_level_template_for_non_target_specialization(self):
        self._create_default_template()
        self.mock_jd_parser.parse.return_value = JDModel(
            metadata=Metadata(
                company=self.COMPANY,
                listing_job_title=self.LISTING_JOB_TITLE,
                role=self.TARGET_ROLE,
                level=self.TARGET_LEVEL,
                specialization="NON-TARGET SPECIALIZATION",
                location="Seattle, WA",
                work_setting=WorkSetting.HYBRID,
            ),
            requirements=self.requirements,
        )

        self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)

        self.assertEqual(Resume.objects.count(), 1)
        resume = Resume.objects.first()
        self.assertEqual(resume.template, self.template)

    def test_run_generates_and_persists_all_resume_roles_and_bullets(self):
        self._create_default_template()

        # Create test roles and configs
        max_bullet_count = 2
        role1 = ExperienceRole.objects.create(key="role1", start_date=self.now, end_date=self.now)
        role2 = ExperienceRole.objects.create(key="role2", start_date=self.now, end_date=self.now)
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

        self.assertEqual(ResumeRole.objects.count(), 2)
        self.assertEqual(ResumeRoleBullet.objects.count(), 4)
        resume_role1 = ResumeRole.objects.filter(source_role=role1).first()
        self.assertIsNotNone(resume_role1)
        resume_role2 = ResumeRole.objects.filter(source_role=role2).first()
        self.assertIsNotNone(resume_role2)
        self.assertTrue(ResumeRoleBullet.objects.filter(resume_role=resume_role1, text=role1_bullet1).exists())
        self.assertTrue(ResumeRoleBullet.objects.filter(resume_role=resume_role1, text=role1_bullet2).exists())
        self.assertTrue(ResumeRoleBullet.objects.filter(resume_role=resume_role2, text=role2_bullet1).exists())
        self.assertTrue(ResumeRoleBullet.objects.filter(resume_role=resume_role2, text=role2_bullet2).exists())

    def test_run_uses_config_title_override_when_present(self):
        self._create_default_template()
        self.mock_resume_writer.generate_experience_bullets.return_value = Mock(bullets=[])
        title_override = "Software Engineer (Backend)"
        role = ExperienceRole.objects.create(start_date=self.now, end_date=self.now)
        TemplateRoleConfig.objects.create(
            title_override=title_override,
            template=self.template,
            experience_role=role,
            order=1,
            max_bullet_count=1,
        )

        self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)

        resume_role = ResumeRole.objects.filter(source_role=role).first()
        self.assertIsNotNone(resume_role)
        self.assertEqual(resume_role.title, title_override)
        
        
    def test_run_generates_and_persists_resume_skills(self):
        self._create_default_template()
        self.mock_resume_writer.generate_skills.return_value = self.skills_model

        self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)

        self.mock_resume_writer.generate_skills.assert_called_once_with(self.template, self.requirements)
        self.assertEqual(ResumeSkillsCategory.objects.count(), len(self.skills))
        self.assertTrue(ResumeSkillsCategory.objects.filter(category=self.SKILLS_CATEGORY1).exists())
        self.assertTrue(ResumeSkillsCategory.objects.filter(category=self.SKILLS_CATEGORY2).exists())

    def test_run_auto_adjusts_to_next_style_for_multi_page_pdf(self):
        ResumeTemplate.objects.create(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            style_path=StylePath.STANDARD,
        )
        self.mock_pdf_reader.side_effect = [
            Mock(pages=[1, 2]), # multi-page
            Mock(pages=[object()]), # single-page
        ]

        self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)
        
        self.assertEqual(self.mock_pdf_reader.call_count, 2)
        resume = Resume.objects.first()
        self.assertEqual(resume.style_path, StylePath.COMPACT)

    def test_run_auto_adjusts_to_final_style_for_multi_page_pdf(self):
        ResumeTemplate.objects.create(
            target_role=self.TARGET_ROLE,
            target_level=self.TARGET_LEVEL,
            style_path=StylePath.STANDARD,
        )
        self.mock_pdf_reader.side_effect = [
            Mock(pages=[1, 2]), # multi-page
            Mock(pages=[1, 2]), # multi-page
            Mock(pages=[object()]), # single-page
        ]

        self.orchestrator.run(self.JD_PATH, auto_open_pdf=False)
        
        self.assertEqual(self.mock_pdf_reader.call_count, 3)
        resume = Resume.objects.first()
        self.assertEqual(resume.style_path, StylePath.DENSE)
