import json
from typing import List

from resume.clients import ClaudeClient
from resume.models import ExperienceProject, ExperienceRole, ResumeTemplate
from resume.schemas import BulletListModel, RequirementSchema, SkillBulletListModel
from resume.utils.prompt import fill_placeholders, load_prompt
from resume.utils.prompt_content_builders import build_requirement_json
from resume.utils.validation import parse_llm_json, validate_with_schema


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
        skill_prompt_path: str = "resume/prompts/generate_skill_bullets.md",
    ):
        """Initialize the resume writer.
        
        Args:
            client: LLM client for API calls. Defaults to ClaudeClient if not provided.
            experience_prompt_path: Path to the experience bullet generation prompt template.
            skill_prompt_path: Path to the skill bullet generation prompt template.
        """
        self.client = client or ClaudeClient()
        self.experience_prompt_path = experience_prompt_path
        self.skill_prompt_path = skill_prompt_path
    
    def generate_experience_bullets(
        self,
        experience_role: ExperienceRole,
        requirements: List[RequirementSchema],
        target_role: str,
        max_bullet_count: int,
        model: str = None,
    ) -> BulletListModel:
        """Generate experience bullets for a specific role tailored to job requirements.
        
        Args:
            experience_role: The ExperienceRole instance to generate bullets for.
            requirements: List of RequirementSchema objects sorted by relevance.
            target_role: The target job role string (e.g., "Software Engineer").
            max_bullet_count: Maximum number of bullets to generate.
            model: Optional LLM model identifier to use for generation.
            
        Returns:
            Validated BulletListModel instance containing generated bullets with order and text.
            
        Raises:
            ValueError: If LLM output is truncated or malformed.
            ValueError: If parsed JSON fails schema validation.
        """
        projects = ExperienceProject.objects.filter(
            experience_role=experience_role
        ).order_by('id')

        if not projects.exists():
            raise ValueError(
                f"No experience projects found for role '{experience_role}'. "
                "Populate the database with relevant projects before generating bullets."
            )
        
        experience_projects_text = self._format_projects_for_prompt(projects)
        requirements_text = build_requirement_json(requirements)
        
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
        parsed_data = parse_llm_json(response_text)
        validated_bullets = validate_with_schema(parsed_data, BulletListModel)
        validated_bullets.validate_max_count(max_bullet_count)
        
        return validated_bullets
    
    def generate_skill_bullets(
        self,
        template: ResumeTemplate,
        requirements: List[RequirementSchema],
        max_category_count: int = 4,
        model: str = None,
    ) -> SkillBulletListModel:
        """Generate skill category bullets for a resume based on requirements and included experience roles.
        
        Args:
            experience_role: The ExperienceRole instance to generate skills for.
            requirements: List of RequirementSchema objects sorted by relevance.
            max_category_count: Maximum number of skill categories to generate.
            model: Optional LLM model identifier to use for generation.
            
        Returns:
            Validated SkillBulletListModel instance containing generated skill categories.
            
        Raises:
            ValueError: If no tools can be extracted from template's configured roles.
            ValueError: If LLM output is truncated or malformed.
            ValueError: If parsed JSON fails schema validation.
        """
        experience_tools = self._format_project_tools_for_prompt(template)
        
        requirement_keywords = json.dumps(list({
            keyword for req in requirements for keyword in req.keywords
        }))
        
        prompt_template = load_prompt(self.skill_prompt_path)
        prompt = fill_placeholders(
            prompt_template,
            {
                "TARGET_ROLE": template.target_role,
                "REQUIREMENTS": requirement_keywords,
                "TOOLS": experience_tools,
            }
        )
        
        response_text = self.client.generate(prompt, model=model, max_tokens=2000)
        parsed_data = parse_llm_json(response_text)
        
        if isinstance(parsed_data, list):
            parsed_data = {"skill_categories": parsed_data}
        
        validated_skills = validate_with_schema(parsed_data, SkillBulletListModel)
        validated_skills.validate_max_count(max_category_count)
        
        return validated_skills
    
    def _format_projects_for_prompt(self, projects: List[ExperienceProject]) -> str:
        """
        Convert a list of ExperienceProject instances into JSON for LLM prompts.

        Args:
            projects: List of ExperienceProject Django model instances.

        Returns:
            JSON string suitable for the EXPERIENCE_PROJECTS placeholder in the LLM prompt.
            Only includes the fields relevant for bullet generation.
        """
        data = [
            {
                "short_name": p.short_name,
                "problem_context": p.problem_context,
                "actions": p.actions,
                "tools": p.tools,
                "outcomes": p.outcomes,
                "impact_area": p.impact_area,
            }
            for p in projects
        ]
        return json.dumps(data, ensure_ascii=False)
    
    def _format_project_tools_for_prompt(self, template: ResumeTemplate) -> str:
        """
        Extract and format all tools from projects associated with a resume template.
        
        Retrieves all tools used across ExperienceProjects for ExperienceRoles configured
        in the given template, deduplicates them, and returns as a JSON-formatted string.
        
        Args:
            template: ResumeTemplate instance to extract tools from
            
        Returns:
            JSON string containing a list of unique tool names
            
        Raises:
            ValueError: If no role configs exist for the template
            ValueError: If no projects exist for the configured roles
            ValueError: If no tools are found in any projects
        """
        role_ids = template.role_configs.values_list("experience_role_id", flat=True)

        if not role_ids.exists():
            raise ValueError(f"No role configs found for template {template}")

        project_tools = ExperienceProject.objects.filter(
            experience_role_id__in=role_ids
        ).values_list('tools', flat=True)
        if not project_tools:
            raise ValueError(f"No projects found for roles in template {template}")
        
        all_tools = set()
        for tools_list in project_tools:
            all_tools.update(tools_list)
        
        if not all_tools:
            raise ValueError(f"No tools found in projects for template {template}")
        
        return json.dumps(list(all_tools))
