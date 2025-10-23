from django.db import IntegrityError
from django.test import TestCase

from resume.models import ExperienceRole, ResumeTemplate, TemplateRoleConfig
from tracker.models.job import JobLevel, JobRole


class TestTemplateRoleConfigModel(TestCase):
    """Test suite for the TemplateRoleConfig model."""

    MAX_BULLET_COUNT = 5
    ORDER = 1

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.template = ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
            template_path="templates/swe_ii.md",
        )
        self.role = ExperienceRole.objects.create(
            key="navit",
            company="Nav.it",
            title="Software Engineer",
        )

    def test_create_template_role_config(self) -> None:
        """Test creating a TemplateRoleConfig instance."""
        config = TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=self.ORDER,
            max_bullet_count=self.MAX_BULLET_COUNT,
        )

        self.assertEqual(config.template, self.template)
        self.assertEqual(config.experience_role, self.role)
        self.assertEqual(config.order, self.ORDER)
        self.assertEqual(config.max_bullet_count, self.MAX_BULLET_COUNT)
        self.assertIsNotNone(config.id)

    def test_str_representation(self) -> None:
        """Test the string representation."""
        config = TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=self.ORDER,
            max_bullet_count=self.MAX_BULLET_COUNT,
        )

        self.assertEqual(str(config), "Software Engineer (II) — navit")

    def test_unique_template_experience_role_constraint(self) -> None:
        """Test that template and experience_role combination must be unique."""
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=self.ORDER,
            max_bullet_count=self.MAX_BULLET_COUNT,
        )

        with self.assertRaises(IntegrityError):
            TemplateRoleConfig.objects.create(
                template=self.template,
                experience_role=self.role,
                order=2,
                max_bullet_count=3,
            )

    def test_multiple_configs_for_same_template(self) -> None:
        """Test creating multiple configs for the same template with different roles."""
        role2 = ExperienceRole.objects.create(
            key="amazon_sde",
            company="Amazon",
            title="Software Development Engineer",
        )

        config1 = TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=self.ORDER,
            max_bullet_count=self.MAX_BULLET_COUNT,
        )
        config2 = TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=role2,
            order=2,
            max_bullet_count=4,
        )

        self.assertEqual(self.template.role_configs.count(), 2)
        self.assertNotEqual(config1.experience_role, config2.experience_role)

    def test_multiple_configs_for_same_role(self) -> None:
        """Test creating multiple configs for the same role across different templates."""
        template2 = ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.SENIOR,
            template_path="templates/swe_senior.md",
        )

        config1 = TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=self.ORDER,
            max_bullet_count=self.MAX_BULLET_COUNT,
        )
        config2 = TemplateRoleConfig.objects.create(
            template=template2,
            experience_role=self.role,
            order=3,
            max_bullet_count=7,
        )

        self.assertEqual(self.role.template_configs.count(), 2)
        self.assertNotEqual(config1.template, config2.template)

    def test_related_name_from_template(self) -> None:
        """Test accessing configs from template via related_name."""
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=self.ORDER,
            max_bullet_count=self.MAX_BULLET_COUNT,
        )

        configs = self.template.role_configs.all()
        self.assertEqual(configs.count(), 1)
        self.assertEqual(configs.first().experience_role, self.role)

    def test_related_name_from_role(self) -> None:
        """Test accessing configs from experience role via related_name."""
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=self.ORDER,
            max_bullet_count=self.MAX_BULLET_COUNT,
        )

        configs = self.role.template_configs.all()
        self.assertEqual(configs.count(), 1)
        self.assertEqual(configs.first().template, self.template)

    def test_order_by_order_field(self) -> None:
        """Test ordering configs by the order field."""
        role2 = ExperienceRole.objects.create(
            key="amazon_sde",
            company="Amazon",
            title="Software Development Engineer",
        )
        role3 = ExperienceRole.objects.create(
            key="google_swe",
            company="Google",
            title="Software Engineer",
        )

        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=role2,
            order=2,
            max_bullet_count=4,
        )
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=1,
            max_bullet_count=self.MAX_BULLET_COUNT,
        )
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=role3,
            order=3,
            max_bullet_count=3,
        )

        configs = self.template.role_configs.order_by("order")
        ordered_roles = [config.experience_role.key for config in configs]
        self.assertEqual(ordered_roles, ["navit", "amazon_sde", "google_swe"])

    def test_cascade_delete_from_template(self) -> None:
        """Test that deleting a template cascades to its configs."""
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=self.ORDER,
            max_bullet_count=self.MAX_BULLET_COUNT,
        )

        self.assertEqual(TemplateRoleConfig.objects.count(), 1)
        self.template.delete()
        self.assertEqual(TemplateRoleConfig.objects.count(), 0)

    def test_cascade_delete_from_role(self) -> None:
        """Test that deleting an experience role cascades to its configs."""
        TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=self.ORDER,
            max_bullet_count=self.MAX_BULLET_COUNT,
        )

        self.assertEqual(TemplateRoleConfig.objects.count(), 1)
        self.role.delete()
        self.assertEqual(TemplateRoleConfig.objects.count(), 0)

    def test_order_field_zero_value(self) -> None:
        """Test that order field accepts zero as a valid value."""
        config = TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=0,
            max_bullet_count=self.MAX_BULLET_COUNT,
        )

        self.assertEqual(config.order, 0)

    def test_multiple_configs_with_same_order(self) -> None:
        """Test creating multiple configs with the same order value."""
        role2 = ExperienceRole.objects.create(
            key="amazon_sde",
            company="Amazon",
            title="Software Development Engineer",
        )

        config1 = TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=self.role,
            order=1,
            max_bullet_count=self.MAX_BULLET_COUNT,
        )
        config2 = TemplateRoleConfig.objects.create(
            template=self.template,
            experience_role=role2,
            order=1,
            max_bullet_count=4,
        )

        self.assertEqual(config1.order, config2.order)
        self.assertEqual(self.template.role_configs.count(), 2)
