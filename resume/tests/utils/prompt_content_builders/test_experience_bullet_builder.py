import pytest

from resume.models.experience_role import ExperienceRole
from resume.models.resume import Resume
from resume.models.resume_experience_bullet import ResumeExperienceBullet
from resume.models.resume_template import ResumeTemplate
from resume.utils.prompt_content_builders.experience_bullet_builder import (
    build_experience_bullets_for_prompt,
)
from tracker.models.job import Job, JobLevel, JobRole, WorkSetting


@pytest.mark.django_db
class TestBuildExperienceBulletsForPrompt:
    """Test suite for build_experience_bullets_for_prompt() helper function."""
    
    @pytest.fixture
    def resume(self) -> Resume:
        """Create a test resume."""
        template = ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
            template_path="templates/test.md"
        )
        job = Job.objects.create(
            company="Test Corp",
            listing_job_title="Software Engineer",
            role=JobRole.SOFTWARE_ENGINEER,
            level=JobLevel.II,
            location="Seattle, WA",
            work_setting=WorkSetting.REMOTE,
            min_experience_years=3
        )
        return Resume.objects.create(
            template=template,
            job=job,
            match_ratio=0.85
        )
    
    @pytest.fixture
    def experience_role(self) -> ExperienceRole:
        """Create a test experience role."""
        return ExperienceRole.objects.create(
            key="test_role",
            company="Previous Corp",
            title="Software Engineer"
        )
    
    def test_formats_single_role_bullets_as_numbered_list(
        self,
        resume: Resume,
        experience_role: ExperienceRole
    ) -> None:
        """Validates formatting of bullets as a numbered list."""
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=experience_role,
            order=1,
            text="First bullet point"
        )
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=experience_role,
            order=2,
            text="Second bullet point"
        )
        
        result = build_experience_bullets_for_prompt(resume)
        
        assert result == "1. First bullet point\n2. Second bullet point"
    
    def test_formats_multiple_role_bullets_without_role_headers(
        self,
        resume: Resume,
        experience_role: ExperienceRole
    ) -> None:
        """Validates bullets from multiple roles are combined into one list."""
        role2 = ExperienceRole.objects.create(
            key="second_role",
            company="Another Corp",
            title="Senior Engineer"
        )
        
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=experience_role,
            order=1,
            text="First role bullet"
        )
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=role2,
            order=1,
            text="Second role bullet"
        )
        
        result = build_experience_bullets_for_prompt(resume)
        
        assert "1. First role bullet" in result
        assert "2. Second role bullet" in result
        assert "**" not in result
    
    def test_excludes_excluded_bullets(
        self,
        resume: Resume,
        experience_role: ExperienceRole
    ) -> None:
        """Ensures excluded bullets are not included in output."""
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=experience_role,
            order=1,
            text="Included bullet",
            exclude=False
        )
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=experience_role,
            order=2,
            text="Excluded bullet",
            exclude=True
        )
        
        result = build_experience_bullets_for_prompt(resume)
        
        assert "Included bullet" in result
        assert "Excluded bullet" not in result
        assert result == "1. Included bullet"
    
    def test_uses_display_text_with_override(
        self,
        resume: Resume,
        experience_role: ExperienceRole
    ) -> None:
        """Ensures override_text is used when available."""
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=experience_role,
            order=1,
            text="Original text",
            override_text="Overridden text"
        )
        
        result = build_experience_bullets_for_prompt(resume)
        
        assert "Overridden text" in result
        assert "Original text" not in result
    
    def test_respects_bullet_order_across_roles(
        self,
        resume: Resume,
        experience_role: ExperienceRole
    ) -> None:
        """Validates bullets are formatted in correct order across roles."""
        role2 = ExperienceRole.objects.create(
            key="second_role",
            company="Another Corp",
            title="Senior Engineer"
        )
        
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=experience_role,
            order=2,
            text="Second bullet from first role"
        )
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=experience_role,
            order=1,
            text="First bullet from first role"
        )
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=role2,
            order=1,
            text="First bullet from second role"
        )
        
        result = build_experience_bullets_for_prompt(resume)
        
        lines = result.split("\n")
        assert "First bullet from first role" in lines[0]
        assert "Second bullet from first role" in lines[1]
        assert "First bullet from second role" in lines[2]
    
    def test_returns_message_for_no_bullets(self, resume: Resume) -> None:
        """Validates behavior when resume has no bullets."""
        result = build_experience_bullets_for_prompt(resume)
        
        assert result == "No experience bullets available."
    
    def test_handles_empty_override_text(
        self,
        resume: Resume,
        experience_role: ExperienceRole
    ) -> None:
        """Ensures empty override_text falls back to text."""
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=experience_role,
            order=1,
            text="Original text",
            override_text="   "
        )
        
        result = build_experience_bullets_for_prompt(resume)
        
        assert "Original text" in result
    
    def test_continuous_numbering_across_multiple_roles(
        self,
        resume: Resume,
        experience_role: ExperienceRole
    ) -> None:
        """Ensures numbering continues across role boundaries."""
        role2 = ExperienceRole.objects.create(
            key="second_role",
            company="Another Corp",
            title="Senior Engineer"
        )
        
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=experience_role,
            order=1,
            text="Bullet one"
        )
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=experience_role,
            order=2,
            text="Bullet two"
        )
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=role2,
            order=1,
            text="Bullet three"
        )
        
        result = build_experience_bullets_for_prompt(resume)
        
        assert "1. Bullet one" in result
        assert "2. Bullet two" in result
        assert "3. Bullet three" in result
   