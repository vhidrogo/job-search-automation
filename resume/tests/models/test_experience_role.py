from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from resume.models.experience_role import ExperienceRole, RoleKey


class TestExperienceRoleModel(TestCase):
    """Test suite for the ExperienceRole model."""

    KEY = RoleKey.NAVIT
    COMPANY = "Nav.it"
    TITLE = "Software Engineer"
    DISPLAY_NAME = "Nav.it SWE"

    def test_create_experience_role(self) -> None:
        """Test creating an ExperienceRole instance."""
        role = ExperienceRole.objects.create(
            key=self.KEY,
            company=self.COMPANY,
            title=self.TITLE,
            display_name=self.DISPLAY_NAME,
        )

        self.assertEqual(role.key, self.KEY)
        self.assertEqual(role.company, self.COMPANY)
        self.assertEqual(role.title, self.TITLE)
        self.assertEqual(role.display_name, self.DISPLAY_NAME)
        self.assertIsNotNone(role.id)

    def test_str_representation_with_display_name(self) -> None:
        """Test the string representation when display_name is set."""
        role = ExperienceRole.objects.create(
            key=self.KEY,
            company=self.COMPANY,
            title=self.TITLE,
            display_name=self.DISPLAY_NAME,
        )

        self.assertEqual(str(role), "Nav.it SWE")

    def test_str_representation_without_display_name(self) -> None:
        """Test the string representation when display_name is empty."""
        role = ExperienceRole.objects.create(
            key=self.KEY,
            company=self.COMPANY,
            title=self.TITLE,
        )

        self.assertEqual(str(role), "Software Engineer – Nav.it")

    def test_default_display_name(self) -> None:
        """Test that display_name defaults to empty string."""
        role = ExperienceRole.objects.create(
            key=self.KEY,
            company=self.COMPANY,
            title=self.TITLE,
        )

        self.assertEqual(role.display_name, "")

    def test_unique_key_constraint(self) -> None:
        """Test that key field must be unique."""
        ExperienceRole.objects.create(
            key=self.KEY,
            company=self.COMPANY,
            title=self.TITLE,
        )

        with self.assertRaises(IntegrityError):
            ExperienceRole.objects.create(
                key=self.KEY,
                company="Different Company",
                title="Different Title",
            )

    def test_all_role_key_choices_valid(self) -> None:
        """Test that all RoleKey choices can be used to create roles."""
        for key_value, key_label in RoleKey.choices:
            role = ExperienceRole.objects.create(
                key=key_value,
                company=f"Company for {key_label}",
                title=f"Title for {key_label}",
            )
            self.assertEqual(role.key, key_value)

    def test_invalid_key_validation(self) -> None:
        """Test that an invalid key choice is rejected."""
        role = ExperienceRole(
            key="invalid_key",
            company=self.COMPANY,
            title=self.TITLE,
        )

        with self.assertRaises(ValidationError):
            role.full_clean()

    def test_query_by_key(self) -> None:
        """Test querying by the key field."""
        role = ExperienceRole.objects.create(
            key=self.KEY,
            company=self.COMPANY,
            title=self.TITLE,
        )

        retrieved = ExperienceRole.objects.get(key=self.KEY)
        self.assertEqual(retrieved.id, role.id)
        self.assertEqual(retrieved.company, self.COMPANY)
