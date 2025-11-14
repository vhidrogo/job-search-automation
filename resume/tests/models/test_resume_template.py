from django.db import IntegrityError
from django.test import TestCase

from resume.models import ResumeTemplate, TargetSpecialization
from tracker.models import JobLevel, JobRole


class TestResumeTemplateModel(TestCase):
    def test_str_with_specialization(self):
        template = ResumeTemplate(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
            target_specialization=TargetSpecialization.BACKEND,
        )
        result = str(template)
        self.assertEqual(result, "Software Engineer II (backend)")

    def test_str_no_specialization(self):
        template = ResumeTemplate(target_role=JobRole.SOFTWARE_ENGINEER, target_level=JobLevel.II)
        result = str(template)
        self.assertEqual(result, "Software Engineer II")

    def test_unique_constraint_with_specialization(self):
        ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
            target_specialization=TargetSpecialization.BACKEND,
        )
        with self.assertRaises(IntegrityError):
            ResumeTemplate.objects.create(
                target_role=JobRole.SOFTWARE_ENGINEER,
                target_level=JobLevel.II,
                target_specialization=TargetSpecialization.BACKEND,
            )

    def test_unique_constraint_no_specialization(self):
        ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
        )
        with self.assertRaises(IntegrityError):
            ResumeTemplate.objects.create(
                target_role=JobRole.SOFTWARE_ENGINEER,
                target_level=JobLevel.II,
            )

    def test_same_role_different_level_allowed(self):
        ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
        )
        ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.I,
        )
        self.assertEqual(ResumeTemplate.objects.count(), 2)

    def test_same_level_different_role_allowed(self):
        ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
        )
        ResumeTemplate.objects.create(
            target_role=JobRole.DATA_ENGINEER,
            target_level=JobLevel.II,
        )
        self.assertEqual(ResumeTemplate.objects.count(), 2)

    def test_same_role_and_level_different_specialization_allowed(self):
        ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
            target_specialization=TargetSpecialization.BACKEND,
        )
        ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
            target_specialization=TargetSpecialization.PYTHON,
        )
        self.assertEqual(ResumeTemplate.objects.count(), 2)
