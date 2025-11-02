from unittest.mock import Mock

from django.test import TestCase

from orchestration.orchestrator import Orchestrator
from resume.models import Resume, ResumeTemplate
from resume.schemas import JDModel, Metadata, RequirementSchema
from resume.services import JDParser, ResumeMatcher, ResumeWriter
from tracker.models import (
    Job,
    JobLevel,
    JobRole,
    WorkSetting
)


class TestOrchestrator(TestCase):
    COMPANY = "Meta"
    JD_PATH = "test/path"

    @classmethod
    def setUpTestData(cls):
        cls.requirements = [
                RequirementSchema(
                    text="5+ years of Python experience",
                    keywords=["Python", "experience"],
                    relevance=0.95,
                    order=1
                ),
                RequirementSchema(
                    text="Experience with Django web framework",
                    keywords=["Django", "web framework"],
                    relevance=0.90,
                    order=2
                ),
        ]

        cls.jd_model = JDModel(
            metadata=Metadata(
                company=cls.COMPANY,
                listing_job_title="Software Engineer",
                role=JobRole.SOFTWARE_ENGINEER,
                level=JobLevel.II,
                location="Seattle, WA",
                work_setting=WorkSetting.HYBRID,
            ),
            requirements=cls.requirements
        )

        ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
        )


    def setUp(self):
        self.mock_jd_parser = Mock(spec=JDParser)
        self.mock_resume_writer = Mock(spec=ResumeWriter)
        self.mock_resumer_matcher = Mock(spec=ResumeMatcher)
        # TODO: mock subprocess with patcher?

        self.mock_jd_parser.parse.return_value = self.jd_model

        self.orchestrator = Orchestrator(
            jd_parser=self.mock_jd_parser,
            resume_writer=self.mock_resume_writer,
            resume_matcher=self.mock_resumer_matcher,
        )

    def test_run_invokes_all_required_services(self):
        self.orchestrator.run(self.JD_PATH)

        self.mock_jd_parser.parse.assert_called_once()

        # TODO: generate bullets called
        # TODO: generate skill bullets called
        # TODO: matcher called
        # TODO: subprocess called?

    def test_run_raises_error_when_resume_template_not_found(self):
        role = JobRole.DATA_ENGINEER
        level = JobLevel.SENIOR
        jd = JDModel(
            metadata=Metadata(
                company="company",
                listing_job_title="listing_job_title",
                role=JobRole.DATA_ENGINEER,
                level=JobLevel.SENIOR,
                location="US",
                work_setting=WorkSetting.REMOTE,
            ),
            requirements=self.requirements,
        )
        self.mock_jd_parser.parse.return_value = jd

        with self.assertRaises(ValueError) as cm:
            self.orchestrator.run(self.JD_PATH)

        error_msg = str(cm.exception)
        self.assertIn("No template found", error_msg)
        self.assertIn(role, error_msg)
        self.assertIn(level, error_msg)

    def test_run_persists_all_models(self):
        self.orchestrator.run(self.JD_PATH)

        # TODO: job model (some details, put in constants?)
        # TODO: requirements (just count)
        # TODO: resume (matches job)
        # TODO: xp bullets (count)
        # TODO: skill bullets
        # Job
        self.assertEqual(Job.objects.count(), 1)
        job = Job.objects.first()
        self.assertEqual(job.company, self.COMPANY)

        # Requirements
        requirements = job.requirements.all()
        self.assertEqual(requirements.count(), 2)

        # Resume
        self.assertEqual(Resume.objects.count(), 1)
        resume = Resume.objects.first()
        self.assertEqual(resume.job, job)

        # Experience Bullets

        # Skill Bullets



    '''
        Test Cases
            - check objects are persisted
                - job
                - requirements
                - resume
            - raises value error for not template found
                - Create Mismatched Job in That Test (if not other JDModel data)

            Notes:
                - set default return values in setUp, then can override in tests if needed
    '''