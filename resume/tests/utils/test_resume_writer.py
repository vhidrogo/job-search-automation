import json
from unittest.mock import MagicMock
import pytest
from resume.models.experience_project import ExperienceProject
from resume.models.experience_role import ExperienceRole
from resume.schemas.experience_bullet_schema import BulletListModel
from resume.utils.resume_writer import ResumeWriter


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
        experience_role: ExperienceRole,
        experience_projects: None
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
        experience_role: ExperienceRole,
        experience_projects: None
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
        experience_role: ExperienceRole,
        experience_projects: None
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
        experience_role: ExperienceRole,
        experience_projects: None
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
        experience_role: ExperienceRole,
        experience_projects: None
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
        experience_role: ExperienceRole,
        experience_projects: None
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
        experience_role: ExperienceRole,
        experience_projects: None
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
        experience_role: ExperienceRole,
        experience_projects: None
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
