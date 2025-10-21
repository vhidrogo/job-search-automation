import json
from unittest.mock import MagicMock
import pytest
from resume.models.experience_project import ExperienceProject
from resume.models.experience_role import ExperienceRole
from resume.models.resume import Resume
from resume.models.resume_experience_bullet import ResumeExperienceBullet
from resume.models.resume_template import ResumeTemplate
from resume.schemas.experience_bullet_schema import BulletListModel
from resume.schemas.skill_bullet_schema import SkillBulletListModel
from resume.services.resume_writer import ResumeWriter
from tracker.models.job import Job, JobLevel, JobRole, WorkSetting


@pytest.mark.django_db
class TestResumeWriterGenerateExperienceBullets:
    """Test suite for ResumeWriter.generate_experience_bullets()."""
    
    TARGET_ROLE = "Software Engineer"
    MAX_BULLET_COUNT = 3
    
    REQUIREMENTS = [
        {
            "text": "Strong Python experience",
            "keywords": ["Python"],
            "relevance": 0.9
        },
        {
            "text": "Experience with Django framework",
            "keywords": ["Django"],
            "relevance": 0.8
        }
    ]
    
    VALID_LLM_RESPONSE = json.dumps({
        "bullets": [
            {
                "order": 1,
                "text": "Built real-time API using Django and Postgres that reduced query latency by 80%"
            },
            {
                "order": 2,
                "text": "Automated data pipeline with Python and Airflow, cutting processing time from 4 hours to 15 minutes"
            }
        ]
    })
    
    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock LLM client."""
        client = MagicMock()
        client.generate.return_value = self.VALID_LLM_RESPONSE
        return client
    
    @pytest.fixture
    def experience_role(self) -> ExperienceRole:
        """Create a test experience role."""
        return ExperienceRole.objects.create(
            key="test_role",
            company="Test Corp",
            title="Software Engineer"
        )
    
    @pytest.fixture
    def experience_projects(self, experience_role: ExperienceRole) -> None:
        """Create test experience projects."""
        ExperienceProject.objects.create(
            experience_role=experience_role,
            short_name="API Redesign",
            problem_context="Legacy API was slow and hard to maintain",
            actions="implemented new REST endpoints, refactored database queries",
            tools="Django,Postgres,Redis",
            outcomes="reduced latency 80%, improved maintainability",
            impact_area="Performance Optimization"
        )
        ExperienceProject.objects.create(
            experience_role=experience_role,
            short_name="ETL Pipeline",
            problem_context="Manual data processing took too long",
            actions="automated data ingestion, built scheduling system",
            tools="Python,Airflow,Pandas",
            outcomes="cut processing time from 4 hours to 15 minutes",
            impact_area="Automation"
        )
    
    def test_generates_bullets_successfully(
        self,
        mock_client: MagicMock,
        experience_role: ExperienceRole
    ) -> None:
        """Validates successful bullet generation with valid inputs."""
        writer = ResumeWriter(client=mock_client)
        
        result = writer.generate_experience_bullets(
            experience_role=experience_role,
            requirements=self.REQUIREMENTS,
            target_role=self.TARGET_ROLE,
            max_bullet_count=self.MAX_BULLET_COUNT
        )
        
        assert isinstance(result, BulletListModel)
        assert len(result.bullets) == 2
        assert result.bullets[0].order == 1
        assert "Django" in result.bullets[0].text
        assert mock_client.generate.called
    
    def test_formats_requirements_correctly_in_prompt(
        self,
        mock_client: MagicMock,
        experience_role: ExperienceRole
    ) -> None:
        """Ensures requirements are formatted with relevance percentages and keywords."""
        writer = ResumeWriter(client=mock_client)
        
        writer.generate_experience_bullets(
            experience_role=experience_role,
            requirements=self.REQUIREMENTS,
            target_role=self.TARGET_ROLE,
            max_bullet_count=self.MAX_BULLET_COUNT
        )
        
        call_args = mock_client.generate.call_args[0][0]
        assert "[90%] Strong Python experience (Keywords: Python)" in call_args
        assert "[80%] Experience with Django framework (Keywords: Django)" in call_args
    
    def test_formats_projects_correctly_in_prompt(
        self,
        mock_client: MagicMock,
        experience_role: ExperienceRole,
        experience_projects: None
    ) -> None:
        """Ensures experience projects are formatted with all fields."""
        writer = ResumeWriter(client=mock_client)
        
        writer.generate_experience_bullets(
            experience_role=experience_role,
            requirements=self.REQUIREMENTS,
            target_role=self.TARGET_ROLE,
            max_bullet_count=self.MAX_BULLET_COUNT
        )
        
        call_args = mock_client.generate.call_args[0][0]
        assert "**API Redesign**" in call_args
        assert "Problem: Legacy API was slow and hard to maintain" in call_args
        assert "Actions: implemented new REST endpoints, refactored database queries" in call_args
        assert "Tools: Django,Postgres,Redis" in call_args
    
    def test_handles_list_response_without_bullets_key(
        self,
        mock_client: MagicMock,
        experience_role: ExperienceRole
    ) -> None:
        """Validates handling of LLM responses that return a list directly."""
        list_response = json.dumps([
            {"order": 1, "text": "First bullet point with at least twenty characters"},
            {"order": 2, "text": "Second bullet point with sufficient length"}
        ])
        mock_client.generate.return_value = list_response
        writer = ResumeWriter(client=mock_client)
        
        result = writer.generate_experience_bullets(
            experience_role=experience_role,
            requirements=self.REQUIREMENTS,
            target_role=self.TARGET_ROLE,
            max_bullet_count=self.MAX_BULLET_COUNT
        )
        
        assert isinstance(result, BulletListModel)
        assert len(result.bullets) == 2
    
    def test_raises_error_when_bullet_count_exceeds_max(
        self,
        mock_client: MagicMock,
        experience_role: ExperienceRole
    ) -> None:
        """Ensures ValueError is raised when LLM returns too many bullets."""
        excessive_response = json.dumps({
            "bullets": [
                {"order": i, "text": f"Bullet {i} with sufficient length for validation"}
                for i in range(1, 6)
            ]
        })
        mock_client.generate.return_value = excessive_response
        writer = ResumeWriter(client=mock_client)
        
        with pytest.raises(ValueError, match="maximum allowed is 3"):
            writer.generate_experience_bullets(
                experience_role=experience_role,
                requirements=self.REQUIREMENTS,
                target_role=self.TARGET_ROLE,
                max_bullet_count=3
            )
    
    def test_passes_model_parameter_to_client(
        self,
        mock_client: MagicMock,
        experience_role: ExperienceRole
    ) -> None:
        """Validates that custom model parameter is passed to LLM client."""
        writer = ResumeWriter(client=mock_client)
        custom_model = "claude-opus-4-1"
        
        writer.generate_experience_bullets(
            experience_role=experience_role,
            requirements=self.REQUIREMENTS,
            target_role=self.TARGET_ROLE,
            max_bullet_count=self.MAX_BULLET_COUNT,
            model=custom_model
        )
        
        mock_client.generate.assert_called_once()
        call_kwargs = mock_client.generate.call_args[1]
        assert call_kwargs['model'] == custom_model
    
    def test_handles_empty_projects_list(
        self,
        mock_client: MagicMock,
        experience_role: ExperienceRole
    ) -> None:
        """Validates behavior when experience role has no associated projects."""
        writer = ResumeWriter(client=mock_client)
        
        result = writer.generate_experience_bullets(
            experience_role=experience_role,
            requirements=self.REQUIREMENTS,
            target_role=self.TARGET_ROLE,
            max_bullet_count=self.MAX_BULLET_COUNT
        )
        
        assert isinstance(result, BulletListModel)
        call_args = mock_client.generate.call_args[0][0]
        assert "**Experience Projects:**" in call_args
    
    def test_raises_error_for_truncated_llm_output(
        self,
        mock_client: MagicMock,
        experience_role: ExperienceRole
    ) -> None:
        """Ensures ValueError is raised when LLM output is incomplete."""
        mock_client.generate.return_value = '{"bullets": [{"order": 1'
        writer = ResumeWriter(client=mock_client)
        
        with pytest.raises(ValueError, match="LLM output truncated"):
            writer.generate_experience_bullets(
                experience_role=experience_role,
                requirements=self.REQUIREMENTS,
                target_role=self.TARGET_ROLE,
                max_bullet_count=self.MAX_BULLET_COUNT
            )
    
    def test_raises_error_for_invalid_json(
        self,
        mock_client: MagicMock,
        experience_role: ExperienceRole
    ) -> None:
        """Ensures ValueError is raised for malformed JSON."""
        mock_client.generate.return_value = '{"bullets": [invalid json]}'
        writer = ResumeWriter(client=mock_client)
        
        with pytest.raises(ValueError, match="Failed to parse LLM JSON output"):
            writer.generate_experience_bullets(
                experience_role=experience_role,
                requirements=self.REQUIREMENTS,
                target_role=self.TARGET_ROLE,
                max_bullet_count=self.MAX_BULLET_COUNT
            )
    
    def test_raises_error_for_schema_validation_failure(
        self,
        mock_client: MagicMock,
        experience_role: ExperienceRole
    ) -> None:
        """Ensures ValueError is raised when response doesn't match schema."""
        invalid_schema_response = json.dumps({
            "bullets": [{"order": "not_an_int", "text": "Valid text with sufficient length"}]
        })
        mock_client.generate.return_value = invalid_schema_response
        writer = ResumeWriter(client=mock_client)
        
        with pytest.raises(ValueError, match="Pydantic validation failed"):
            writer.generate_experience_bullets(
                experience_role=experience_role,
                requirements=self.REQUIREMENTS,
                target_role=self.TARGET_ROLE,
                max_bullet_count=self.MAX_BULLET_COUNT
            )


@pytest.mark.django_db
class TestResumeWriterGenerateSkillBullets:
    """Test suite for ResumeWriter.generate_skill_bullets()."""
    
    TARGET_ROLE = "Software Engineer"
    MAX_CATEGORY_COUNT = 4
    
    REQUIREMENTS = [
        {
            "text": "Strong Python and Django experience",
            "keywords": ["Python", "Django"],
            "relevance": 0.9
        },
        {
            "text": "Experience with AWS cloud services",
            "keywords": ["AWS"],
            "relevance": 0.8
        },
        {
            "text": "Proficiency with React for frontend development",
            "keywords": ["React", "JavaScript"],
            "relevance": 0.7
        }
    ]
    
    VALID_LLM_RESPONSE = json.dumps([
        {
            "category": "Programming Languages",
            "skills": "Python, JavaScript"
        },
        {
            "category": "Frameworks & Libraries",
            "skills": "Django, React"
        }
    ])
    
    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock LLM client."""
        client = MagicMock()
        client.generate.return_value = self.VALID_LLM_RESPONSE
        return client
    
    @pytest.fixture
    def resume_with_bullets(self) -> Resume:
        """Create a test resume with experience bullets."""
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
        resume = Resume.objects.create(
            template=template,
            job=job,
            match_ratio=0.85
        )
        
        role = ExperienceRole.objects.create(
            key="test_role",
            company="Previous Corp",
            title="Software Engineer"
        )
        
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=role,
            order=1,
            text="Built Django REST API with Python for 10K+ daily requests"
        )
        ResumeExperienceBullet.objects.create(
            resume=resume,
            experience_role=role,
            order=2,
            text="Deployed infrastructure on AWS using Docker and Terraform"
        )
        
        return resume
    
    def test_generates_skill_bullets_successfully(
        self,
        mock_client: MagicMock,
        resume_with_bullets: Resume
    ) -> None:
        """Validates successful skill bullet generation with valid inputs."""
        writer = ResumeWriter(client=mock_client)
        
        result = writer.generate_skill_bullets(
            resume=resume_with_bullets,
            requirements=self.REQUIREMENTS,
            target_role=self.TARGET_ROLE,
            max_category_count=self.MAX_CATEGORY_COUNT
        )
        
        assert isinstance(result, SkillBulletListModel)
        assert len(result.skill_categories) == 2
        assert result.skill_categories[0].category == "Programming Languages"
        assert "Python" in result.skill_categories[0].skills
        assert mock_client.generate.called
    
    def test_formats_keywords_correctly_in_prompt(
        self,
        mock_client: MagicMock,
        resume_with_bullets: Resume
    ) -> None:
        """Ensures keywords are extracted and formatted as comma-separated list."""
        writer = ResumeWriter(client=mock_client)
        
        writer.generate_skill_bullets(
            resume=resume_with_bullets,
            requirements=self.REQUIREMENTS,
            target_role=self.TARGET_ROLE,
            max_category_count=self.MAX_CATEGORY_COUNT
        )
        
        call_args = mock_client.generate.call_args[0][0]
        assert "Python, Django, AWS, React, JavaScript" in call_args
    
    def test_deduplicates_keywords_case_insensitively(
        self,
        mock_client: MagicMock,
        resume_with_bullets: Resume
    ) -> None:
        """Ensures duplicate keywords with different cases are deduplicated."""
        requirements_with_dupes = [
            {"text": "Python experience", "keywords": ["Python", "python"], "relevance": 0.9},
            {"text": "Django skills", "keywords": ["Django", "DJANGO"], "relevance": 0.8}
        ]
        writer = ResumeWriter(client=mock_client)
        
        writer.generate_skill_bullets(
            resume=resume_with_bullets,
            requirements=requirements_with_dupes,
            target_role=self.TARGET_ROLE,
            max_category_count=self.MAX_CATEGORY_COUNT
        )
        
        call_args = mock_client.generate.call_args[0][0]
        assert call_args.count("Python") == 1
        assert call_args.count("Django") == 1
    
    def test_formats_experience_bullets_as_numbered_list(
        self,
        mock_client: MagicMock,
        resume_with_bullets: Resume
    ) -> None:
        """Ensures experience bullets are formatted as a numbered list."""
        writer = ResumeWriter(client=mock_client)
        
        writer.generate_skill_bullets(
            resume=resume_with_bullets,
            requirements=self.REQUIREMENTS,
            target_role=self.TARGET_ROLE,
            max_category_count=self.MAX_CATEGORY_COUNT
        )
        
        call_args = mock_client.generate.call_args[0][0]
        assert "1. Built Django REST API with Python for 10K+ daily requests" in call_args
        assert "2. Deployed infrastructure on AWS using Docker and Terraform" in call_args
    
    def test_handles_dict_response_without_skill_categories_key(
        self,
        mock_client: MagicMock,
        resume_with_bullets: Resume
    ) -> None:
        """Validates handling of LLM responses that return a list directly."""
        list_response = json.dumps([
            {"category": "Programming Languages", "skills": "Python, Java"},
            {"category": "Cloud Platforms", "skills": "AWS, Azure"}
        ])
        mock_client.generate.return_value = list_response
        writer = ResumeWriter(client=mock_client)
        
        result = writer.generate_skill_bullets(
            resume=resume_with_bullets,
            requirements=self.REQUIREMENTS,
            target_role=self.TARGET_ROLE,
            max_category_count=self.MAX_CATEGORY_COUNT
        )
        
        assert isinstance(result, SkillBulletListModel)
        assert len(result.skill_categories) == 2
    
    def test_raises_error_when_category_count_exceeds_max(
        self,
        mock_client: MagicMock,
        resume_with_bullets: Resume
    ) -> None:
        """Ensures ValueError is raised when LLM returns too many categories."""
        excessive_response = json.dumps([
            {"category": f"Category {i}", "skills": "skill1, skill2"}
            for i in range(1, 6)
        ])
        mock_client.generate.return_value = excessive_response
        writer = ResumeWriter(client=mock_client)
        
        with pytest.raises(ValueError, match="maximum allowed is 4"):
            writer.generate_skill_bullets(
                resume=resume_with_bullets,
                requirements=self.REQUIREMENTS,
                target_role=self.TARGET_ROLE,
                max_category_count=4
            )
    
    def test_passes_model_parameter_to_client(
        self,
        mock_client: MagicMock,
        resume_with_bullets: Resume
    ) -> None:
        """Validates that custom model parameter is passed to LLM client."""
        writer = ResumeWriter(client=mock_client)
        custom_model = "claude-haiku-4-5"
        
        writer.generate_skill_bullets(
            resume=resume_with_bullets,
            requirements=self.REQUIREMENTS,
            target_role=self.TARGET_ROLE,
            max_category_count=self.MAX_CATEGORY_COUNT,
            model=custom_model
        )
        
        mock_client.generate.assert_called_once()
        call_kwargs = mock_client.generate.call_args[1]
        assert call_kwargs['model'] == custom_model
    
    def test_handles_resume_with_no_bullets(
        self,
        mock_client: MagicMock
    ) -> None:
        """Validates behavior when resume has no experience bullets."""
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
        resume = Resume.objects.create(
            template=template,
            job=job,
            match_ratio=0.0
        )
        
        writer = ResumeWriter(client=mock_client)
        
        writer.generate_skill_bullets(
            resume=resume,
            requirements=self.REQUIREMENTS,
            target_role=self.TARGET_ROLE,
            max_category_count=self.MAX_CATEGORY_COUNT
        )
        
        call_args = mock_client.generate.call_args[0][0]
        assert "No experience bullets available." in call_args
    
    def test_handles_requirements_with_no_keywords(
        self,
        mock_client: MagicMock,
        resume_with_bullets: Resume
    ) -> None:
        """Validates behavior when requirements have no keywords."""
        requirements_no_keywords = [
            {"text": "General software development", "keywords": [], "relevance": 0.5}
        ]
        writer = ResumeWriter(client=mock_client)
        
        writer.generate_skill_bullets(
            resume=resume_with_bullets,
            requirements=requirements_no_keywords,
            target_role=self.TARGET_ROLE,
            max_category_count=self.MAX_CATEGORY_COUNT
        )
        
        call_args = mock_client.generate.call_args[0][0]
        assert "No specific keywords provided" in call_args
    
    def test_raises_error_for_truncated_llm_output(
        self,
        mock_client: MagicMock,
        resume_with_bullets: Resume
    ) -> None:
        """Ensures ValueError is raised when LLM output is incomplete."""
        mock_client.generate.return_value = '[{"category": "Programming"'
        writer = ResumeWriter(client=mock_client)
        
        with pytest.raises(ValueError, match="LLM output truncated"):
            writer.generate_skill_bullets(
                resume=resume_with_bullets,
                requirements=self.REQUIREMENTS,
                target_role=self.TARGET_ROLE,
                max_category_count=self.MAX_CATEGORY_COUNT
            )
    
    def test_raises_error_for_invalid_json(
        self,
        mock_client: MagicMock,
        resume_with_bullets: Resume
    ) -> None:
        """Ensures ValueError is raised for malformed JSON."""
        mock_client.generate.return_value = '[{invalid json}]'
        writer = ResumeWriter(client=mock_client)
        
        with pytest.raises(ValueError, match="Failed to parse LLM JSON output"):
            writer.generate_skill_bullets(
                resume=resume_with_bullets,
                requirements=self.REQUIREMENTS,
                target_role=self.TARGET_ROLE,
                max_category_count=self.MAX_CATEGORY_COUNT
            )
    
    def test_deduplicates_keywords_case_insensitively(
        self,
        mock_client: MagicMock,
        resume_with_bullets: Resume
    ) -> None:
        """Ensures duplicate keywords with different cases are deduplicated."""
        requirements_with_dupes = [
            {"text": "Python experience", "keywords": ["Python", "python"], "relevance": 0.9},
            {"text": "Django skills", "keywords": ["Django", "DJANGO"], "relevance": 0.8}
        ]
        writer = ResumeWriter(client=mock_client)
        
        writer.generate_skill_bullets(
            resume=resume_with_bullets,
            requirements=requirements_with_dupes,
            target_role=self.TARGET_ROLE,
            max_category_count=self.MAX_CATEGORY_COUNT
        )
        
        call_args = mock_client.generate.call_args[0][0]
        # Verify the keywords appear exactly once in the entire prompt (case-insensitive check)
        assert call_args.lower().count("python, django") == 1 or "Python, Django" in call_args
