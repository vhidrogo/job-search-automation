from typing import List

from resume.clients import ClaudeClient
from resume.models import ExperienceProject, ExperienceRole, Resume
from resume.schemas import BulletListModel, RequirementSchema, SkillBulletListModel
from resume.utils.prompt import fill_placeholders, load_prompt
from resume.utils.prompt_content_builders import build_experience_bullets_for_prompt
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
        parsed_data = parse_llm_json(response_text)
        
        if isinstance(parsed_data, list):
            parsed_data = {"bullets": parsed_data}
        
        validated_bullets = validate_with_schema(parsed_data, BulletListModel)
        validated_bullets.validate_max_count(max_bullet_count)
        
        return validated_bullets
    
    def generate_skill_bullets(
        self,
        resume: Resume,
        requirements: List[RequirementSchema],
        target_role: str,
        max_category_count: int,
        model: str = None,
    ) -> SkillBulletListModel:
        """Generate skill category bullets for a resume based on requirements and experience bullets.
        
        Args:
            resume: The Resume instance whose experience bullets will be analyzed.
            requirements: List of RequirementSchema objects sorted by relevance.
            target_role: The target job role string (e.g., "Software Engineer").
            max_category_count: Maximum number of skill categories to generate.
            model: Optional LLM model identifier to use for generation.
            
        Returns:
            Validated SkillBulletListModel instance containing generated skill categories.
            
        Raises:
            ValueError: If LLM output is truncated or malformed.
            ValueError: If parsed JSON fails schema validation.
        """
        bullets_text = build_experience_bullets_for_prompt(resume)
        keywords_text = self._format_keywords_for_prompt(requirements)
        
        prompt_template = load_prompt(self.skill_prompt_path)
        prompt = fill_placeholders(
            prompt_template,
            {
                "TARGET_ROLE": target_role,
                "REQUIREMENTS": keywords_text,
                "BULLETS": bullets_text,
            }
        )
        
        response_text = self.client.generate(prompt, model=model, max_tokens=2000)
        parsed_data = parse_llm_json(response_text)
        
        if isinstance(parsed_data, list):
            parsed_data = {"skill_categories": parsed_data}
        
        validated_skills = validate_with_schema(parsed_data, SkillBulletListModel)
        validated_skills.validate_max_count(max_category_count)
        
        return validated_skills
    
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
    
    def _format_requirements_for_prompt(self, requirements: List[RequirementSchema]) -> str:
        """Format requirements list into numbered prompt text with relevance scores.
        
        Args:
            requirements: List of RequirementSchema objects sorted by relevance.
            
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
    
    def _format_keywords_for_prompt(self, requirements: List[RequirementSchema]) -> str:
        """Extract and format keywords from requirements into comma-separated text.
        
        Args:
            requirements: List of RequirementSchema objects sorted by relevance.
            
        Returns:
            Comma-separated string of unique keywords from all requirements.
        """
        all_keywords = []
        for req in requirements:
            keywords = req.get('keywords', [])
            all_keywords.extend(keywords)
        
        unique_keywords = []
        seen = set()
        for keyword in all_keywords:
            if keyword.lower() not in seen:
                seen.add(keyword.lower())
                unique_keywords.append(keyword)
        
        return ", ".join(unique_keywords) if unique_keywords else "No specific keywords provided"
