from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from resume.models import ExperienceRole, ResumeTemplate, TemplateRoleConfig
from tracker.models.job import JobLevel, JobRole


class TestTemplateRoleConfigModel(TestCase):
    TARGET_ROLE = JobRole.SOFTWARE_ENGINEER
    TARGET_LEVEL = JobLevel.II
    COMPANY = "Amazon.com"
    TITLE = "Software Engineer"

    @classmethod
    def setUpTestData(cls):
        cls.template = ResumeTemplate.objects.create(
            target_role=cls.TARGET_ROLE,
            target_level=cls.TARGET_LEVEL,
        )
        cls.role = ExperienceRole.objects.create(
            company=cls.COMPANY,
            title=cls.TITLE,
            start_date=timezone.now(), 
            end_date=timezone.now(),
        )

        cls.other_role = ExperienceRole.objects.create(
            key="other role",
            start_date=timezone.now(), 
            end_date=timezone.now(),
        )
        
    def test_str(self):
        config = TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            max_bullet_count=1,
            order=1,
        )
        self.assertEqual(str(config), "Software Engineer II (Software Engineer - Amazon.com)")

    def test_unique_template_experience_role_constraint(self):
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            max_bullet_count=1,
            order=1,
        )

        with self.assertRaises(IntegrityError):
            TemplateRoleConfig.objects.create(
                template=self.template,
                experience_role=self.role,
                max_bullet_count=1,
                order=2,
            )

    def test_same_template_different_experience_role_allowed(self):
        config1 = TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            max_bullet_count=1,
            order=1,
        )
        config2 = TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.other_role,
            max_bullet_count=1,
            order=2,
        )
        self.assertEqual(TemplateRoleConfig.objects.count(), 2)
        self.assertEqual(config1.template, config2.template)
        self.assertNotEqual(config1.experience_role, config2.experience_role)


    def test_unique_template_order_constraint(self):
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            max_bullet_count=1,
            order=1,
        )

        with self.assertRaises(IntegrityError):
            TemplateRoleConfig.objects.create(
                template=self.template,
                experience_role=self.other_role,
                max_bullet_count=1,
                order=1,
            )

    def test_same_template_different_order_allowed(self):
        config1 = TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            max_bullet_count=1,
            order=1,
        )
        config2 = TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.other_role,
            max_bullet_count=1,
            order=2,
        )
        self.assertEqual(TemplateRoleConfig.objects.count(), 2)
        self.assertEqual(config1.template, config2.template)
        self.assertNotEqual(config1.order, config2.order)
