import json
from unittest.mock import ANY, Mock

from django.test import TestCase
from django.utils import timezone

from resume.clients import ClaudeClient
from resume.models import (
    Resume,
    ResumeRole,
    ResumeRoleBullet,
    ResumeSkillsCategory,
    ResumeTemplate,
    ExperienceProject,
    ExperienceRole,
)
from tracker.models import (
    Application,
    Interview,
    InterviewPreparationBase,
    Job,
    JobRole,
    JobLevel,
    LlmRequestLog,
)
from tracker.schemas import InterviewPrepBaseSchema, InterviewPrepSpecificSchema
from tracker.services import InterviewPrepGenerator


class TestInterviewPrepGenerator(TestCase):
    RAW_JD_TEXT = "Software Engineer II position requiring Python and AWS experience"
    FORMATTED_JD = "# Job Description\n**Python** required"
    COMPANY_CONTEXT = "## What the company does\nPet care marketplace"
    PRIMARY_DRIVERS = "**Python Experience**: 2+ years with Django"
    BACKGROUND_NARRATIVE = "### Opening one-liner\nSoftware engineer with backend focus"
    RESUME_DEFENSE_PREP = "Resume defense prep"
    PREP_PLAN = "### Study Materials"
    PREDICTED_QUESTIONS = "### Question 1\nTell me about a time..."
    INTERVIEWER_QUESTIONS = "### Question 1\nWhat does success look like?"
    TECHNICAL_DEEP_DIVES = "Technical deep dives"
    ROLE_TITLE = "Software Engineer"
    RESUME_BULLET = "Built API with Django"

    @classmethod
    def setUpTestData(cls):
        cls.job = Job.objects.create(raw_jd_text=cls.RAW_JD_TEXT)
        cls.application = Application.objects.create(job=cls.job)
        cls.interview_stage = Interview.Stage.RECRUITER_SCREEN.label
        cls.interview_focus = Interview.Focus.BEHAVIORAL.label
        cls.interviewer_title = "Recruiter"
        cls.interview = Interview.objects.create(
            application=cls.application,
            stage=cls.interview_stage,
            focus=cls.interview_focus,
            interviewer_title=cls.interviewer_title,
            scheduled_at=timezone.now(),
        )
        
        template = ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
        )
        cls.resume = Resume.objects.create(
            template=template,
            job=cls.job,
        )
        cls.experience_role = ExperienceRole.objects.create(
            title=cls.ROLE_TITLE,
            start_date=timezone.now(),
            end_date=timezone.now(),
        )
        resume_role = ResumeRole.objects.create(
            resume=cls.resume,
            source_role=cls.experience_role,
            title=cls.ROLE_TITLE,
            order=1,
        )
        ResumeRoleBullet.objects.create(
            resume_role=resume_role,
            text=cls.RESUME_BULLET,
            order=1,
        )
        ResumeSkillsCategory.objects.create(
            resume=cls.resume,
            order=1,
            category="Programming Languages",
            skills_text="Python, Java",
        )

        cls.base_response = json.dumps({
            "formatted_jd": cls.FORMATTED_JD,
            "company_context": cls.COMPANY_CONTEXT,
            "primary_drivers": cls.PRIMARY_DRIVERS,
            "background_narrative": cls.BACKGROUND_NARRATIVE,
            "resume_defense_prep": cls.RESUME_DEFENSE_PREP,
        })

        cls.specific_response = json.dumps({
            "prep_plan": cls.PREP_PLAN,
            "predicted_questions": cls.PREDICTED_QUESTIONS,
            "interviewer_questions": cls.INTERVIEWER_QUESTIONS,
            "technical_deep_dives": cls.TECHNICAL_DEEP_DIVES,
        })

    def setUp(self):
        self.mock_client = Mock(spec=ClaudeClient)
        self.generator = InterviewPrepGenerator(client=self.mock_client)

    def test_generate_base_preparation_returns_validated_schema(self):
        self.mock_client.generate.return_value = self.base_response

        result = self.generator.generate_base_preparation(self.application)

        self.mock_client.generate.assert_called_once_with(
            ANY,
            call_type=LlmRequestLog.CallType.GENERATE_INTERVIEW_PREP_BASE,
            model=ANY,
            max_tokens=ANY,
        )
        expected = InterviewPrepBaseSchema(
            formatted_jd=self.FORMATTED_JD,
            company_context=self.COMPANY_CONTEXT,
            primary_drivers=self.PRIMARY_DRIVERS,
            background_narrative=self.BACKGROUND_NARRATIVE,
            resume_defense_prep=self.RESUME_DEFENSE_PREP,
        )
        self.assertEqual(result, expected)

    def test_generate_base_preparation_raises_when_no_resume(self):
        job = Job.objects.create()
        application = Application.objects.create(job=job)

        with self.assertRaises(ValueError) as cm:
            self.generator.generate_base_preparation(application)

        self.assertIn("no associated resume", str(cm.exception))

    def test_generate_base_preparation_raises_on_invalid_json(self):
        self.mock_client.generate.return_value = "invalid json"

        with self.assertRaises(ValueError):
            self.generator.generate_base_preparation(self.application)

    def test_generate_base_preparation_builds_prompt_with_jd_and_resume(self):
        self.mock_client.generate.return_value = self.base_response

        self.generator.generate_base_preparation(self.application)

        prompt = self._get_prompt_arg()
        self.assertIn(self.RAW_JD_TEXT, prompt)
        self.assertIn(self.ROLE_TITLE, prompt)
        self.assertIn("EXPERIENCE", prompt)
        self.assertIn(self.RESUME_BULLET, prompt)
        self.assertIn("SKILLS", prompt)
        self.assertIn("Programming Languages: Python, Java", prompt)

    def test_generate_base_preparation_includes_resume_projects_json(self):
        project = ExperienceProject.objects.create(
            experience_role=self.experience_role,
            problem_context="Scaling API bottleneck",
            actions="Refactored query layer",
            tools="Django, Postgres",
            outcomes="Reduced latency by 40%",
        )
        bullet = ResumeRoleBullet.objects.first()
        bullet.experience_project = project
        bullet.save()
        self.mock_client.generate.return_value = self.base_response

        self.generator.generate_base_preparation(self.application)

        prompt = self._get_prompt_arg()
        self.assertIn("Scaling API bottleneck", prompt)
        self.assertIn("Refactored query layer", prompt)
        self.assertIn("Django, Postgres", prompt)
        self.assertIn("Reduced latency by 40%", prompt)

    def test_generate_interview_preparation_returns_validated_schema(self):
        InterviewPreparationBase.objects.create(application=self.application)
        self.mock_client.generate.return_value = self.specific_response

        result = self.generator.generate_interview_preparation(self.interview)

        self.mock_client.generate.assert_called_once_with(
            ANY,
            call_type=LlmRequestLog.CallType.GENERATE_INTERVIEW_PREP_SPECIFIC,
            model=ANY,
            max_tokens=ANY,
        )
        expected = InterviewPrepSpecificSchema(
            prep_plan=self.PREP_PLAN,
            predicted_questions=self.PREDICTED_QUESTIONS,
            interviewer_questions=self.INTERVIEWER_QUESTIONS,
            technical_deep_dives=self.TECHNICAL_DEEP_DIVES,
        )
        self.assertEqual(result, expected)

    def test_generate_interview_preparation_raises_when_no_base_prep(self):
        with self.assertRaises(ValueError) as cm:
            self.generator.generate_interview_preparation(self.interview)

        error_msg = str(cm.exception)
        self.assertIn("Base preparation must exist", error_msg)
        self.assertIn(str(self.application.id), error_msg)

    def test_generate_interview_preparation_raises_when_no_resume(self):
        job = Job.objects.create()
        application = Application.objects.create(job=job)
        InterviewPreparationBase.objects.create(application=application)
        interview = Interview.objects.create(
            application=application,
            scheduled_at=timezone.now(),
        )

        with self.assertRaises(ValueError) as cm:
            self.generator.generate_interview_preparation(interview)

        self.assertIn("no associated resume", str(cm.exception))

    def test_generate_interview_preparation_raises_on_invalid_json(self):
        InterviewPreparationBase.objects.create(application=self.application)
        self.mock_client.generate.return_value = "invalid json"

        with self.assertRaises(ValueError):
            self.generator.generate_interview_preparation(self.interview)

    def test_generate_interview_preparation_builds_prompt_with_all_context(self):
        InterviewPreparationBase.objects.create(
            application=self.application,
            formatted_jd=self.FORMATTED_JD,
            primary_drivers=self.PRIMARY_DRIVERS,
        )
        self.mock_client.generate.return_value = self.specific_response

        self.generator.generate_interview_preparation(self.interview)
        prompt = self._get_prompt_arg()
        self.assertIn(self.RAW_JD_TEXT, prompt)
        self.assertIn("EXPERIENCE", prompt)
        self.assertIn(self.RESUME_BULLET, prompt)
        self.assertIn(self.PRIMARY_DRIVERS, prompt)
        self.assertIn(self.interview_stage, prompt)
        self.assertIn(self.interview_focus, prompt)
        self.assertIn(self.interviewer_title, prompt)

    def test_generate_interview_preparation_includes_resume_projects_json(self):
        InterviewPreparationBase.objects.create(application=self.application)
        project = ExperienceProject.objects.create(
            experience_role=self.experience_role,
            problem_context="Scaling API bottleneck",
            actions="Refactored query layer",
            tools="Django, Postgres",
            outcomes="Reduced latency by 40%",
        )
        bullet = ResumeRoleBullet.objects.first()
        bullet.experience_project = project
        bullet.save()
        self.mock_client.generate.return_value = self.specific_response

        self.generator.generate_interview_preparation(self.interview)

        prompt = self._get_prompt_arg()
        self.assertIn("Scaling API bottleneck", prompt)
        self.assertIn("Refactored query layer", prompt)
        self.assertIn("Django, Postgres", prompt)
        self.assertIn("Reduced latency by 40%", prompt)

    def test_generate_interview_preparation_includes_prior_interview_notes(self):
        InterviewPreparationBase.objects.create(application=self.application)
        Interview.objects.create(
            application=self.application,
            stage=Interview.Stage.TECHNICAL_SCREEN,
            focus=Interview.Focus.CODING,
            scheduled_at=timezone.now() - timezone.timedelta(days=7),
            notes="Struggled with graph traversal",
        )
        self.mock_client.generate.return_value = self.specific_response

        self.generator.generate_interview_preparation(self.interview)

        prompt = self._get_prompt_arg()
        self.assertIn("Technical Screen", prompt)
        self.assertIn("Coding", prompt)
        self.assertIn("Struggled with graph traversal", prompt)

    def test_generate_interview_preparation_excludes_empty_notes(self):
        InterviewPreparationBase.objects.create(application=self.application)
        Interview.objects.create(
            application=self.application,
            scheduled_at=timezone.now() - timezone.timedelta(days=7),
            notes="",
        )
        self.mock_client.generate.return_value = self.specific_response

        self.generator.generate_interview_preparation(self.interview)

        prompt = self._get_prompt_arg()
        self.assertNotIn('"notes": ""', prompt)

    def _get_prompt_arg(self):
        self.mock_client.generate.assert_called_once()
        return self.mock_client.generate.call_args[0][0]
