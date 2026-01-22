from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from tracker.models import Application, Interview, InterviewPreparation, InterviewPreparationBase, Job
from tracker.schemas import InterviewPrepBaseSchema, InterviewPrepSpecificSchema
from tracker.utils import generate_base_prep_for_application, generate_prep_for_interview


class TestGenerateBasePrepForApplication(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.job = Job.objects.create()
        cls.application = Application.objects.create(job=cls.job)

    @patch("tracker.utils.interview_prep.InterviewPrepGenerator.generate_base_preparation")
    def test_generate_base_prep_for_application_creates_prep_base(self, mock_generator):
        mock_generator.return_value = InterviewPrepBaseSchema(
            formatted_jd="jd",
            company_context="company",
            primary_drivers="drivers",
            background_narrative="background",
        )

        created = generate_base_prep_for_application(self.application.id)

        mock_generator.assert_called_once_with(self.application)
        self.assertTrue(created)
        self.assertEqual(InterviewPreparationBase.objects.count(), 1)
        obj = InterviewPreparationBase.objects.first()
        self.assertEqual(obj.application.id, self.application.id)

    def test_generate_base_prep_for_application_does_not_generate_if_existing_prep_base(self):
        InterviewPreparationBase.objects.create(application=self.application)
        created = generate_base_prep_for_application(self.application.id)
        self.assertFalse(created)


class TestGeneratePrepForInterview(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.job = Job.objects.create()
        cls.application = Application.objects.create(job=cls.job)
        cls.interview = Interview.objects.create(application=cls.application, scheduled_at=timezone.now())

    @patch("tracker.utils.interview_prep.InterviewPrepGenerator.generate_interview_preparation")
    def test_generate_prep_for_interview_creates_prep(self, mock_generator):
        mock_generator.return_value = InterviewPrepSpecificSchema(
            prep_plan="prep_plan",
            predicted_questions="predicted_questions",
            interviewer_questions="interviewer_questions",
            resume_defense_prep="resume_defense_prep",
            technical_deep_dives="technical_deep_dives",
        )

        created = generate_prep_for_interview(self.interview.id)

        mock_generator.assert_called_once_with(self.interview)
        self.assertTrue(created)
        self.assertEqual(InterviewPreparation.objects.count(), 1)
        obj = InterviewPreparation.objects.first()
        self.assertEqual(obj.interview.id, self.interview.id)

    def test_generate_prep_for_interview_does_not_generate_if_existing_prep(self):
        InterviewPreparation.objects.create(interview=self.interview)
        created = generate_prep_for_interview(self.interview.id)
        self.assertFalse(created)
