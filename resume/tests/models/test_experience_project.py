from django.test import TestCase
from django.utils import timezone

from resume.models import ExperienceProject, ExperienceRole


class TestExperienceProjectModel(TestCase):
    def test_str(self):
        role = ExperienceRole.objects.create(
            title="Software Development Engineer",
            company="Amazon.com",
            start_date=timezone.now(),
            end_date=timezone.now(),
        )
        project = ExperienceProject.objects.create(
            experience_role=role,
            short_name="REST API Development"
        )
        self.assertEqual(str(project), "REST API Development (Software Development Engineer - Amazon.com)")
        