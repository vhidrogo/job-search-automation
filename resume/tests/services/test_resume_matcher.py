import json
from unittest.mock import MagicMock
import pytest
from resume.models import Resume
from resume.models import ResumeSkillBullet, ResumeTemplate
from resume.schemas import MatchResultSchema
from resume.services.resume_matcher import ResumeMatcher
from tracker.models import Job, JobLevel, JobRole, Requirement, WorkSetting


@pytest.mark.django_db
class TestResumeMatcherEvaluate:
    """Test suite for ResumeMatcher.evaluate()."""
    
    VALID_LLM_RESPONSE = json.dumps({
        "unmet_requirements": "Go, Kubernetes",
        "match_ratio": 0.75
    })
    
    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock LLM client."""
        client = MagicMock()
        client.generate.return_value = self.VALID_LLM_RESPONSE
        return client
    
    @pytest.fixture
    def job_with_requirements(self) -> Job:
        """Create a test job with requirements."""
        job = Job.objects.create(
            company="Test Corp",
            listing_job_title="Software Engineer",
            role=JobRole.SOFTWARE_ENGINEER,
            level=JobLevel.II,
            location="Seattle, WA",
            work_setting=WorkSetting.REMOTE,
            min_experience_years=3
        )
        
        Requirement.objects.create(
            job=job,
            text="Strong Python experience",
            keywords=["Python", "Django"],
            relevance=0.9,
            order=1
        )
        Requirement.objects.create(
            job=job,
            text="AWS cloud services",
            keywords=["AWS", "EC2", "S3"],
            relevance=0.8,
            order=2
        )
        Requirement.objects.create(
            job=job,
            text="Container orchestration",
            keywords=["Kubernetes", "Docker"],
            relevance=0.7,
            order=3
        )
        Requirement.objects.create(
            job=job,
            text="Go programming",
            keywords=["Go", "Golang"],
            relevance=0.6,
            order=4
        )
        
        return job
    
    @pytest.fixture
    def resume_with_skills(self, job_with_requirements: Job) -> Resume:
        """Create a test resume with skill bullets."""
        template = ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
            template_path="templates/test.md"
        )
        
        resume = Resume.objects.create(
            template=template,
            job=job_with_requirements,
            match_ratio=0.0
        )
        
        ResumeSkillBullet.objects.create(
            resume=resume,
            category="Programming Languages",
            skills_text="Python, JavaScript, Java"
        )
        ResumeSkillBullet.objects.create(
            resume=resume,
            category="Frameworks & Libraries",
            skills_text="Django, React, Flask"
        )
        ResumeSkillBullet.objects.create(
            resume=resume,
            category="Cloud & DevOps",
            skills_text="AWS, Docker, Terraform"
        )
        
        return resume
    
    def test_evaluates_match_successfully(
        self,
        mock_client: MagicMock,
        resume_with_skills: Resume
    ) -> None:
        """Validates successful match evaluation with valid inputs."""
        matcher = ResumeMatcher(client=mock_client)
        
        result = matcher.evaluate(job_id=resume_with_skills.job.id)
        
        assert isinstance(result, MatchResultSchema)
        assert result.match_ratio == 0.75
        assert result.unmet_requirements == "Go, Kubernetes"
        assert mock_client.generate.called
    
    def test_formats_requirements_keywords_as_separate_lines(
        self,
        mock_client: MagicMock,
        resume_with_skills: Resume
    ) -> None:
        """Ensures each requirement's keywords appear as numbered list items."""
        matcher = ResumeMatcher(client=mock_client)
        
        matcher.evaluate(job_id=resume_with_skills.job.id)
        
        call_args = mock_client.generate.call_args[0][0]
        assert "1. Python, Django" in call_args
        assert "2. AWS, EC2, S3" in call_args
        assert "3. Kubernetes, Docker" in call_args
        assert "4. Go, Golang" in call_args
    
    def test_preserves_requirement_order(
        self,
        mock_client: MagicMock,
        resume_with_skills: Resume
    ) -> None:
        """Ensures requirements are ordered by their order field."""
        matcher = ResumeMatcher(client=mock_client)
        
        matcher.evaluate(job_id=resume_with_skills.job.id)
        
        call_args = mock_client.generate.call_args[0][0]
        python_index = call_args.index("Python, Django")
        aws_index = call_args.index("AWS, EC2, S3")
        k8s_index = call_args.index("Kubernetes, Docker")
        go_index = call_args.index("Go, Golang")
        
        assert python_index < aws_index < k8s_index < go_index
    
    def test_formats_skill_keywords_correctly(
        self,
        mock_client: MagicMock,
        resume_with_skills: Resume
    ) -> None:
        """Ensures skill keywords are formatted as comma-separated list."""
        matcher = ResumeMatcher(client=mock_client)
        
        matcher.evaluate(job_id=resume_with_skills.job.id)
        
        call_args = mock_client.generate.call_args[0][0]
        assert "Python, JavaScript, Java, Django, React, Flask, AWS, Docker, Terraform" in call_args
    
    def test_deduplicates_skill_keywords_case_insensitively(
        self,
        mock_client: MagicMock,
        job_with_requirements: Job
    ) -> None:
        """Ensures duplicate skill keywords with different cases are deduplicated."""
        template = ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
            template_path="templates/test.md"
        )
        resume = Resume.objects.create(
            template=template,
            job=job_with_requirements,
            match_ratio=0.0
        )
        
        ResumeSkillBullet.objects.create(
            resume=resume,
            category="Programming Languages",
            skills_text="Python, python, PYTHON"
        )
        ResumeSkillBullet.objects.create(
            resume=resume,
            category="Frameworks",
            skills_text="Django, django"
        )
        
        matcher = ResumeMatcher(client=mock_client)
        matcher.evaluate(job_id=job_with_requirements.id)
        
        call_args = mock_client.generate.call_args[0][0]
        skills_section_start = call_args.index("**Skill Keywords:**")
        skills_section = call_args[skills_section_start:]
        assert skills_section.count("Python") == 1
        assert skills_section.count("Django") == 1
    
    def test_handles_perfect_match(
        self,
        mock_client: MagicMock,
        resume_with_skills: Resume
    ) -> None:
        """Validates handling of 100% match with no unmet requirements."""
        perfect_match_response = json.dumps({
            "unmet_requirements": "",
            "match_ratio": 1.0
        })
        mock_client.generate.return_value = perfect_match_response
        matcher = ResumeMatcher(client=mock_client)
        
        result = matcher.evaluate(job_id=resume_with_skills.job.id)
        
        assert result.match_ratio == 1.0
        assert result.unmet_requirements == ""
    
    def test_handles_zero_match(
        self,
        mock_client: MagicMock,
        resume_with_skills: Resume
    ) -> None:
        """Validates handling of 0% match with all requirements unmet."""
        zero_match_response = json.dumps({
            "unmet_requirements": "Python, Django, AWS, EC2, S3, Kubernetes, Docker, Go, Golang",
            "match_ratio": 0.0
        })
        mock_client.generate.return_value = zero_match_response
        matcher = ResumeMatcher(client=mock_client)
        
        result = matcher.evaluate(job_id=resume_with_skills.job.id)
        
        assert result.match_ratio == 0.0
        assert len(result.unmet_requirements) > 0
    
    def test_rounds_match_ratio_to_two_decimals(
        self,
        mock_client: MagicMock,
        resume_with_skills: Resume
    ) -> None:
        """Ensures match ratio is rounded to 2 decimal places."""
        precise_response = json.dumps({
            "unmet_requirements": "Go",
            "match_ratio": 0.876543
        })
        mock_client.generate.return_value = precise_response
        matcher = ResumeMatcher(client=mock_client)
        
        result = matcher.evaluate(job_id=resume_with_skills.job.id)
        
        assert result.match_ratio == 0.88
    
    def test_passes_model_parameter_to_client(
        self,
        mock_client: MagicMock,
        resume_with_skills: Resume
    ) -> None:
        """Validates that custom model parameter is passed to LLM client."""
        matcher = ResumeMatcher(client=mock_client)
        custom_model = "claude-haiku-4-5"
        
        matcher.evaluate(job_id=resume_with_skills.job.id, model=custom_model)
        
        mock_client.generate.assert_called_once()
        call_kwargs = mock_client.generate.call_args[1]
        assert call_kwargs['model'] == custom_model
    
    def test_handles_job_with_no_requirements(
        self,
        mock_client: MagicMock
    ) -> None:
        """Validates behavior when job has no requirements."""
        job = Job.objects.create(
            company="Test Corp",
            listing_job_title="Software Engineer",
            role=JobRole.SOFTWARE_ENGINEER,
            level=JobLevel.II,
            location="Seattle, WA",
            work_setting=WorkSetting.REMOTE,
            min_experience_years=3
        )
        template = ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
            template_path="templates/test.md"
        )
        resume = Resume.objects.create(
            template=template,
            job=job,
            match_ratio=0.0
        )
        
        matcher = ResumeMatcher(client=mock_client)
        matcher.evaluate(job_id=job.id)
        
        call_args = mock_client.generate.call_args[0][0]
        assert "No requirements specified" in call_args
    
    def test_handles_resume_with_no_skills(
        self,
        mock_client: MagicMock,
        job_with_requirements: Job
    ) -> None:
        """Validates behavior when resume has no skill bullets."""
        template = ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
            template_path="templates/test.md"
        )
        resume = Resume.objects.create(
            template=template,
            job=job_with_requirements,
            match_ratio=0.0
        )
        
        matcher = ResumeMatcher(client=mock_client)
        matcher.evaluate(job_id=job_with_requirements.id)
        
        call_args = mock_client.generate.call_args[0][0]
        assert "No skills available" in call_args
    
    def test_raises_error_for_truncated_llm_output(
        self,
        mock_client: MagicMock,
        resume_with_skills: Resume
    ) -> None:
        """Ensures ValueError is raised when LLM output is incomplete."""
        mock_client.generate.return_value = '{"unmet_requirements": "Go"'
        matcher = ResumeMatcher(client=mock_client)
        
        with pytest.raises(ValueError, match="LLM output truncated"):
            matcher.evaluate(job_id=resume_with_skills.job.id)
    
    def test_raises_error_for_invalid_json(
        self,
        mock_client: MagicMock,
        resume_with_skills: Resume
    ) -> None:
        """Ensures ValueError is raised for malformed JSON."""
        mock_client.generate.return_value = '{invalid json}'
        matcher = ResumeMatcher(client=mock_client)
        
        with pytest.raises(ValueError, match="Failed to parse LLM JSON output"):
            matcher.evaluate(job_id=resume_with_skills.job.id)
    
    def test_raises_error_for_schema_validation_failure(
        self,
        mock_client: MagicMock,
        resume_with_skills: Resume
    ) -> None:
        """Ensures ValueError is raised when response doesn't match schema."""
        invalid_schema_response = json.dumps({
            "unmet_requirements": "Go",
            "match_ratio": 1.5
        })
        mock_client.generate.return_value = invalid_schema_response
        matcher = ResumeMatcher(client=mock_client)
        
        with pytest.raises(ValueError, match="Pydantic validation failed"):
            matcher.evaluate(job_id=resume_with_skills.job.id)
    
    def test_handles_requirements_with_empty_keywords_list(
        self,
        mock_client: MagicMock,
        job_with_requirements: Job
    ) -> None:
        """Validates behavior when a requirement has an empty keywords list."""
        Requirement.objects.create(
            job=job_with_requirements,
            text="General experience",
            keywords=[],
            relevance=0.3,
            order=5
        )
        
        template = ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
            template_path="templates/test.md"
        )
        resume = Resume.objects.create(
            template=template,
            job=job_with_requirements,
            match_ratio=0.0
        )
        ResumeSkillBullet.objects.create(
            resume=resume,
            category="Programming",
            skills_text="Python"
        )
        
        matcher = ResumeMatcher(client=mock_client)
        result = matcher.evaluate(job_id=job_with_requirements.id)
        
        assert isinstance(result, MatchResultSchema)
        call_args = mock_client.generate.call_args[0][0]
        requirements_section = call_args.split("**Requirement Keywords:**")[1].split("**Skill Keywords:**")[0]
        requirement_lines = [line.strip() for line in requirements_section.strip().split("\n") if line.strip()]
        assert len(requirement_lines) == 4

    def test_skips_requirements_with_no_keywords(
        self,
        mock_client: MagicMock,
        job_with_requirements: Job
    ) -> None:
        """Validates that requirements with empty keywords are excluded from prompt."""
        Requirement.objects.create(
            job=job_with_requirements,
            text="General software experience",
            keywords=[],
            relevance=0.5,
            order=5
        )
        
        template = ResumeTemplate.objects.create(
            target_role=JobRole.SOFTWARE_ENGINEER,
            target_level=JobLevel.II,
            template_path="templates/test.md"
        )
        resume = Resume.objects.create(
            template=template,
            job=job_with_requirements,
            match_ratio=0.0
        )
        ResumeSkillBullet.objects.create(
            resume=resume,
            category="Programming",
            skills_text="Python"
        )
        
        matcher = ResumeMatcher(client=mock_client)
        matcher.evaluate(job_id=job_with_requirements.id)
        
        call_args = mock_client.generate.call_args[0][0]
        requirements_section = call_args.split("**Requirement Keywords:**")[1].split("**Skill Keywords:**")[0]
        requirement_lines = [line.strip() for line in requirements_section.strip().split("\n") if line.strip()]
        assert len(requirement_lines) == 4
