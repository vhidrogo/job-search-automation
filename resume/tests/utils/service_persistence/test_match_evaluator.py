from django.test import TestCase
from unittest.mock import patch

from resume.models import Resume, ResumeTemplate
from resume.schemas import MatchResultSchema
from resume.utils.service_persistence import evaluate_and_update_match
from tracker.models import Job


class TestEvaluateAndUpdateMatch(TestCase):
    def setUp(self):
        self.job = Job.objects.create()
        template = ResumeTemplate.objects.create()
        self.resume = Resume.objects.create(    
            job=self.job,
            template=template,
            )
         
    @patch("resume.utils.service_persistence.match_evaluator.ResumeMatcher")
    def test_resume_match_is_updated(self, mock_matcher_class):
        unmet_requirements = "Rust, Ruby on Rails"
        match_ratio = .9
        mock_instance = mock_matcher_class.return_value
        mock_instance.evaluate.return_value = MatchResultSchema(
            unmet_requirements=unmet_requirements,
            match_ratio=match_ratio,
        )

        evaluate_and_update_match(self.job.id)

        mock_instance.evaluate.assert_called_once_with(self.job.id)
        self.resume.refresh_from_db()
        self.assertEqual(self.resume.unmet_requirements, unmet_requirements)
        self.assertEqual(self.resume.match_ratio, match_ratio)
