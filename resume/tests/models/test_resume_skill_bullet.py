from django.test import TestCase

from resume.models import Resume, ResumeSkillBullet, ResumeTemplate
from tracker.models import Job, JobLevel, JobRole, WorkSetting


class TestResumeSkillBulletModel(TestCase):
    """Test suite for the ResumeSkillBullet model."""

    COMPANY = "Meta"
    LISTING_JOB_TITLE = "Software Engineer"
    ROLE = JobRole.SOFTWARE_ENGINEER
    LEVEL = JobLevel.II
    LOCATION = "Seattle, WA"
    WORK_SETTING = WorkSetting.REMOTE
    MIN_EXPERIENCE_YEARS = 3
    TEMPLATE_PATH = "templates/software_engineer_ii.md"
    MATCH_RATIO = 0.85
    CATEGORY = "Programming Languages"
    SKILLS_TEXT = "Python, Java, TypeScript"

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
            match_ratio=self.MATCH_RATIO,
        )

    def test_create_skill_bullet(self) -> None:
        """Test creating a ResumeSkillBullet instance."""
        bullet = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text=self.SKILLS_TEXT,
        )

        self.assertEqual(bullet.resume, self.resume)
        self.assertEqual(bullet.category, self.CATEGORY)
        self.assertEqual(bullet.skills_text, self.SKILLS_TEXT)
        self.assertIsNotNone(bullet.id)

    def test_str_representation(self) -> None:
        """Test the string representation of ResumeSkillBullet."""
        bullet = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text=self.SKILLS_TEXT,
        )

        self.assertEqual(
            str(bullet),
            "Programming Languages for Meta: Python, Java, TypeScript..."
        )

    def test_skills_list_display(self) -> None:
        """Test skills_list_display() returns trimmed skills text."""
        bullet = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text=self.SKILLS_TEXT,
        )

        self.assertEqual(bullet.skills_list_display(), self.SKILLS_TEXT)

    def test_skills_list_display_strips_whitespace(self) -> None:
        """Test skills_list_display() strips leading/trailing whitespace."""
        bullet = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text=f"  {self.SKILLS_TEXT}  ",
        )

        self.assertEqual(bullet.skills_list_display(), self.SKILLS_TEXT)

    def test_skills_list_returns_list(self) -> None:
        """Test skills_list() returns list of individual skills."""
        bullet = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text=self.SKILLS_TEXT,
        )

        expected = ["Python", "Java", "TypeScript"]
        self.assertEqual(bullet.skills_list(), expected)

    def test_skills_list_strips_individual_skills(self) -> None:
        """Test skills_list() strips whitespace from individual skills."""
        bullet = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text="  Python  ,  Java  , TypeScript  ",
        )

        expected = ["Python", "Java", "TypeScript"]
        self.assertEqual(bullet.skills_list(), expected)

    def test_skills_list_empty_string(self) -> None:
        """Test skills_list() returns empty list for empty string."""
        bullet = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text="",
        )

        self.assertEqual(bullet.skills_list(), [])

    def test_skills_list_whitespace_only(self) -> None:
        """Test skills_list() returns empty list for whitespace-only string."""
        bullet = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text="   ",
        )

        self.assertEqual(bullet.skills_list(), [])

    def test_skills_list_filters_empty_items(self) -> None:
        """Test skills_list() filters out empty items from CSV."""
        bullet = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text="Python,,Java,  ,TypeScript",
        )

        expected = ["Python", "Java", "TypeScript"]
        self.assertEqual(bullet.skills_list(), expected)

    def test_cascade_delete_on_resume_deletion(self) -> None:
        """Test that deleting resume cascades to skill bullets."""
        ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text=self.SKILLS_TEXT,
        )

        self.assertEqual(ResumeSkillBullet.objects.count(), 1)
        self.resume.delete()
        self.assertEqual(ResumeSkillBullet.objects.count(), 0)

    def test_related_name_from_resume(self) -> None:
        """Test accessing skill bullets from resume via related_name."""
        bullet = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text=self.SKILLS_TEXT,
        )

        self.assertIn(bullet, self.resume.skill_bullets.all())

    def test_multiple_skill_bullets_same_resume(self) -> None:
        """Test creating multiple skill bullets for the same resume."""
        bullet1 = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text=self.SKILLS_TEXT,
        )
        bullet2 = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category="Databases",
            skills_text="PostgreSQL, MongoDB",
        )

        self.assertEqual(self.resume.skill_bullets.count(), 2)
        self.assertIn(bullet1, self.resume.skill_bullets.all())
        self.assertIn(bullet2, self.resume.skill_bullets.all())

    def test_filter_by_category(self) -> None:
        """Test filtering skill bullets by category."""
        lang_bullet = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category="Programming Languages",
            skills_text="Python, Java",
        )
        db_bullet = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category="Databases",
            skills_text="PostgreSQL, MySQL",
        )

        lang_bullets = ResumeSkillBullet.objects.filter(
            category="Programming Languages"
        )
        db_bullets = ResumeSkillBullet.objects.filter(category="Databases")

        self.assertIn(lang_bullet, lang_bullets)
        self.assertNotIn(db_bullet, lang_bullets)
        self.assertIn(db_bullet, db_bullets)
        self.assertNotIn(lang_bullet, db_bullets)

    def test_str_truncates_long_skills_text(self) -> None:
        """Test string representation truncates long skills text."""
        long_skills = "Python, Java, JavaScript, TypeScript, C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, Scala"
        bullet = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text=long_skills,
        )

        str_repr = str(bullet)
        self.assertTrue(len(str_repr) < len(long_skills) + 100)
        self.assertIn("...", str_repr)

    def test_multiple_resumes_different_skill_bullets(self) -> None:
        """Test skill bullets are isolated per resume."""
        other_job = Job.objects.create(
            company="Amazon",
            listing_job_title="Data Engineer",
            role=JobRole.DATA_ENGINEER,
            level=self.LEVEL,
            location="New York, NY",
            work_setting=WorkSetting.HYBRID,
            min_experience_years=5,
        )
        other_resume = Resume.objects.create(
            template=self.template,
            job=other_job,
            match_ratio=0.75,
        )

        bullet1 = ResumeSkillBullet.objects.create(
            resume=self.resume,
            category=self.CATEGORY,
            skills_text=self.SKILLS_TEXT,
        )
        bullet2 = ResumeSkillBullet.objects.create(
            resume=other_resume,
            category="Data Processing",
            skills_text="Spark, Hadoop",
        )

        self.assertEqual(self.resume.skill_bullets.count(), 1)
        self.assertEqual(other_resume.skill_bullets.count(), 1)
        self.assertIn(bullet1, self.resume.skill_bullets.all())
        self.assertNotIn(bullet2, self.resume.skill_bullets.all())
