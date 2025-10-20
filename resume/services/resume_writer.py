from typing import Dict, List
from resume.models.experience_project import ExperienceProject
from resume.models.experience_role import ExperienceRole
from resume.schemas.experience_bullet_schema import BulletListModel
from resume.clients.llm_client import ClaudeClient
from resume.utils.prompt import fill_placeholders, load_prompt
from resume.utils.llm_helpers import (
    parse_json_response,
    validate_with_schema,
)


class ResumeWriter:
    """Generates tailored resume content using LLM-based bullet and skill generation.
    
    This service coordinates LLM calls to produce experience bullets and skill bullets
    for resumes. It uses role-specific experience projects and job requirements to
    generate contextually relevant, high-quality resume content that aligns with
    target job descriptions.
    """
    
    def __init__(
        self,
        client: ClaudeClient = None,
        experience_prompt_path: str = "resume/prompts/generate_experience_bullets.md",
    ):
        """Initialize the resume writer.
        
        Args:
            client: LLM client for API calls. Defaults to ClaudeClient if not provided.
            experience_prompt_path: Path to the experience bullet generation prompt template.
        """
        self.client = client or ClaudeClient()
        self.experience_prompt_path = experience_prompt_path
    
    def generate_experience_bullets(
        self,
        experience_role: ExperienceRole,
        requirements: List[Dict[str, any]],
        target_role: str,
        max_bullet_count: int,
        model: str = None,
    ) -> BulletListModel:
        """Generate experience bullets for a specific role tailored to job requirements.
        
        Args:
            experience_role: The ExperienceRole instance to generate bullets for.
            requirements: List of requirement dictionaries with 'text', 'keywords', 
                         and 'relevance' keys, sorted by relevance (highest first).
            target_role: The target job role string (e.g., "Software Engineer").
            max_bullet_count: Maximum number of bullets to generate.
            model: Optional LLM model identifier to use for generation.
            
        Returns:
            Validated BulletListModel instance containing generated bullets with order and text.
            
        Raises:
            ValueError: If LLM output is truncated or malformed.
            ValueError: If parsed JSON fails schema validation.
        """
        # Query and structure experience projects for this role
        projects = ExperienceProject.objects.filter(
            experience_role=experience_role
        ).order_by('id')
        
        experience_projects_text = self._format_projects_for_prompt(projects)
        requirements_text = self._format_requirements_for_prompt(requirements)
        
        prompt_template = load_prompt(self.experience_prompt_path)
        prompt = fill_placeholders(
            prompt_template,
            {
                "MAX_BULLET_COUNT": str(max_bullet_count),
                "TARGET_ROLE": target_role,
                "REQUIREMENTS": requirements_text,
                "EXPERIENCE_PROJECTS": experience_projects_text,
            }
        )
        
        response_text = self.client.generate(prompt, model=model, max_tokens=4000)
        parsed_data = parse_json_response(response_text)
        
        if isinstance(parsed_data, list):
            parsed_data = {"bullets": parsed_data}
        
        validated_bullets = validate_with_schema(parsed_data, BulletListModel)
        validated_bullets.validate_max_count(max_bullet_count)
        
        return validated_bullets
    
    def _format_requirements_for_prompt(self, requirements: List[Dict[str, any]]) -> str:
        """Format requirements list into numbered prompt text with relevance scores.
        
        Args:
            requirements: List of requirement dicts with 'text', 'keywords', and 'relevance'.
            
        Returns:
            Formatted string with numbered requirements, relevance percentages, and keywords.
        """
        requirements_lines = []
        for idx, req in enumerate(requirements, start=1):
            relevance_pct = int(req.get('relevance', 0) * 100)
            keywords_str = ", ".join(req.get('keywords', []))
            req_line = f"{idx}. [{relevance_pct}%] {req['text']}"
            if keywords_str:
                req_line += f" (Keywords: {keywords_str})"
            requirements_lines.append(req_line)
        
        return "\n".join(requirements_lines)
    
    def _format_projects_for_prompt(self, projects) -> str:
        """Format experience projects into structured prompt text blocks.
        
        Args:
            projects: QuerySet of ExperienceProject instances.
            
        Returns:
            Formatted string with project blocks containing problem, actions, tools, outcomes, and impact.
        """
        project_blocks = []
        for project in projects:
            project_block = (
                f"**{project.short_name}**\n"
                f"- Problem: {project.problem_context}\n"
                f"- Actions: {project.actions}\n"
                f"- Tools: {project.tools}\n"
                f"- Outcomes: {project.outcomes}\n"
                f"- Impact Area: {project.impact_area}"
            )
            project_blocks.append(project_block)
        
        return "\n\n".join(project_blocks)
