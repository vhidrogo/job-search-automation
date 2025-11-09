from django.test import TestCase
from django.utils import timezone

from resume.models import (
    ExperienceRole,
    Resume,
    ResumeExperienceBullet,
    ResumeTemplate,
)
from tracker.models.job import Job, JobLevel, JobRole, WorkSetting


class TestResumeExperienceBulletModel(TestCase):
    """Test suite for the ResumeExperienceBullet model."""

    COMPANY = "Meta"
    LISTING_JOB_TITLE = "Software Engineer"
    ROLE = JobRole.SOFTWARE_ENGINEER
    LEVEL = JobLevel.II
    LOCATION = "Seattle, WA"
    WORK_SETTING = WorkSetting.REMOTE
    MIN_EXPERIENCE_YEARS = 3
    TEMPLATE_PATH = "templates/software_engineer_ii.md"
    EXPERIENCE_KEY = "navit_swe"
    EXPERIENCE_COMPANY = "Nav.it"
    EXPERIENCE_TITLE = "Software Engineer"
    BULLET_TEXT = "Implemented a Django-based REST API serving 10K+ requests per day"
    BULLET_ORDER = 1
    OVERRIDE_TEXT = "Built and deployed a Django REST API handling 10K+ daily requests"

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.template = ResumeTemplate.objects.create(
            target_role=self.ROLE,
            target_level=self.LEVEL,
            template_path=self.TEMPLATE_PATH,
        )
        self.job = Job.objects.create(
            company=self.COMPANY,
            listing_job_title=self.LISTING_JOB_TITLE,
            role=self.ROLE,
            level=self.LEVEL,
            location=self.LOCATION,
            work_setting=self.WORK_SETTING,
            min_experience_years=self.MIN_EXPERIENCE_YEARS,
        )
        self.resume = Resume.objects.create(
            template=self.template,
            job=self.job,
        )
        self.experience_role = ExperienceRole.objects.create(
            key=self.EXPERIENCE_KEY,
            company=self.EXPERIENCE_COMPANY,
            title=self.EXPERIENCE_TITLE,
            start_date=timezone.now(),
            end_date=timezone.now(),
        )

    def test_create_experience_bullet(self) -> None:
        """Test creating a ResumeExperienceBullet instance."""
        bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=self.BULLET_TEXT,
        )

        self.assertEqual(bullet.resume, self.resume)
        self.assertEqual(bullet.experience_role, self.experience_role)
        self.assertEqual(bullet.order, self.BULLET_ORDER)
        self.assertEqual(bullet.text, self.BULLET_TEXT)
        self.assertFalse(bullet.exclude)
        self.assertEqual(bullet.override_text, "")
        self.assertIsNotNone(bullet.id)

    def test_str_representation(self) -> None:
        """Test the string representation of ResumeExperienceBullet."""
        bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=self.BULLET_TEXT,
        )

        self.assertEqual(
            str(bullet),
            "Bullet 1 for Meta: Implemented a Django-based REST API serving 10K+ r..."
        )

    def test_str_representation_with_exclude(self) -> None:
        """Test string representation includes exclusion marker."""
        bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=self.BULLET_TEXT,
            exclude=True,
        )

        self.assertEqual(
            str(bullet),
            "Bullet 1 for Meta [EXCLUDED]: Implemented a Django-based REST API serving 10K+ r..."
        )

    def test_default_values(self) -> None:
        """Test default field values."""
        bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=self.BULLET_TEXT,
        )

        self.assertFalse(bullet.exclude)
        self.assertEqual(bullet.override_text, "")

    def test_display_text_without_override(self) -> None:
        """Test display_text() returns text when no override exists."""
        bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=self.BULLET_TEXT,
        )

        self.assertEqual(bullet.display_text(), self.BULLET_TEXT)

    def test_display_text_with_override(self) -> None:
        """Test display_text() returns override_text when set."""
        bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=self.BULLET_TEXT,
            override_text=self.OVERRIDE_TEXT,
        )

        self.assertEqual(bullet.display_text(), self.OVERRIDE_TEXT)

    def test_display_text_strips_whitespace(self) -> None:
        """Test display_text() strips leading/trailing whitespace."""
        bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=f"  {self.BULLET_TEXT}  ",
        )

        self.assertEqual(bullet.display_text(), self.BULLET_TEXT)

    def test_display_text_override_strips_whitespace(self) -> None:
        """Test display_text() strips whitespace from override_text."""
        bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=self.BULLET_TEXT,
            override_text=f"  {self.OVERRIDE_TEXT}  ",
        )

        self.assertEqual(bullet.display_text(), self.OVERRIDE_TEXT)

    def test_display_text_empty_override_falls_back_to_text(self) -> None:
        """Test display_text() uses text when override_text is whitespace-only."""
        bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=self.BULLET_TEXT,
            override_text="   ",
        )

        self.assertEqual(bullet.display_text(), self.BULLET_TEXT)

    def test_ordering_by_order_field(self) -> None:
        """Test bullets are ordered by the order field."""
        bullet2 = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=2,
            text="Second bullet",
        )
        bullet1 = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=1,
            text="First bullet",
        )
        bullet3 = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=3,
            text="Third bullet",
        )

        bullets = list(ResumeExperienceBullet.objects.all())
        self.assertEqual(bullets[0].id, bullet1.id)
        self.assertEqual(bullets[1].id, bullet2.id)
        self.assertEqual(bullets[2].id, bullet3.id)

    def test_cascade_delete_on_resume_deletion(self) -> None:
        """Test that deleting resume cascades to bullets."""
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=self.BULLET_TEXT,
        )

        self.assertEqual(ResumeExperienceBullet.objects.count(), 1)
        self.resume.delete()
        self.assertEqual(ResumeExperienceBullet.objects.count(), 0)

    def test_cascade_delete_on_experience_role_deletion(self) -> None:
        """Test that deleting experience role cascades to bullets."""
        ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=self.BULLET_TEXT,
        )

        self.assertEqual(ResumeExperienceBullet.objects.count(), 1)
        self.experience_role.delete()
        self.assertEqual(ResumeExperienceBullet.objects.count(), 0)

    def test_related_name_from_resume(self) -> None:
        """Test accessing bullets from resume via related_name."""
        bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=self.BULLET_TEXT,
        )

        self.assertIn(bullet, self.resume.experience_bullets.all())

    def test_related_name_from_experience_role(self) -> None:
        """Test accessing bullets from experience role via related_name."""
        bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=self.BULLET_TEXT,
        )

        self.assertIn(bullet, self.experience_role.resume_bullets.all())

    def test_multiple_bullets_same_resume(self) -> None:
        """Test creating multiple bullets for the same resume."""
        bullet1 = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=1,
            text="First bullet",
        )
        bullet2 = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=2,
            text="Second bullet",
        )

        self.assertEqual(self.resume.experience_bullets.count(), 2)
        self.assertIn(bullet1, self.resume.experience_bullets.all())
        self.assertIn(bullet2, self.resume.experience_bullets.all())

    def test_query_by_resume_and_order(self) -> None:
        """Test querying bullets by resume and order."""
        bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=self.BULLET_ORDER,
            text=self.BULLET_TEXT,
        )

        retrieved = ResumeExperienceBullet.objects.get(
            resume=self.resume, order=self.BULLET_ORDER
        )
        self.assertEqual(retrieved.id, bullet.id)

    def test_exclude_flag_functionality(self) -> None:
        """Test exclude flag can be set and queried."""
        excluded_bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=1,
            text="Excluded bullet",
            exclude=True,
        )
        included_bullet = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=2,
            text="Included bullet",
            exclude=False,
        )

        excluded_bullets = ResumeExperienceBullet.objects.filter(exclude=True)
        included_bullets = ResumeExperienceBullet.objects.filter(exclude=False)

        self.assertIn(excluded_bullet, excluded_bullets)
        self.assertNotIn(excluded_bullet, included_bullets)
        self.assertIn(included_bullet, included_bullets)
        self.assertNotIn(included_bullet, excluded_bullets)

    def test_filter_by_experience_role(self) -> None:
        """Test filtering bullets by experience role."""
        other_role = ExperienceRole.objects.create(
            key="amazon_sde",
            company="Amazon",
            start_date=timezone.now(),
            end_date=timezone.now(),
        )

        bullet1 = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=self.experience_role,
            order=1,
            text="Nav.it bullet",
        )
        bullet2 = ResumeExperienceBullet.objects.create(
            resume=self.resume,
            experience_role=other_role,
            order=2,
            text="Amazon bullet",
        )

        navit_bullets = ResumeExperienceBullet.objects.filter(
            experience_role=self.experience_role
        )
        amazon_bullets = ResumeExperienceBullet.objects.filter(
            experience_role=other_role
        )

        self.assertIn(bullet1, navit_bullets)
        self.assertNotIn(bullet2, navit_bullets)
        self.assertIn(bullet2, amazon_bullets)
        self.assertNotIn(bullet1, amazon_bullets)
