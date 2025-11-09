from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from resume.models import ExperienceRole


class TestExperienceRoleModel(TestCase):
    def setUp(self):
        self.start_date = timezone.now()
        self.end_date = timezone.now()

    def test_str(self):
        role = ExperienceRole.objects.create(
            title="Software Engineer",
            company="Nav.it",
            start_date=self.start_date,
            end_date=self.end_date,
            )
        self.assertEqual(str(role), "Software Engineer - Nav.it")

    def test_unique_key_constraint(self):
        key = "key"
        ExperienceRole.objects.create(
            key=key,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        with self.assertRaises(IntegrityError):
            ExperienceRole.objects.create(
                key=key,
                start_date=self.start_date,
                end_date=self.end_date,
            )
    def test_multiple_roles_with_different_keys(self):
        role1 = ExperienceRole.objects.create(
            key="key",
            start_date=self.start_date,
            end_date=self.end_date,
        )
        role2 = ExperienceRole.objects.create(
            key="other key",
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.assertEqual(ExperienceRole.objects.count(), 2)
        self.assertNotEqual(role1.key, role2.key)
