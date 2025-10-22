from resume.clients.llm_client import ClaudeClient
from resume.models import Resume, ResumeSkillBullet
from resume.schemas import MatchResultSchema
from resume.utils.prompt import fill_placeholders, load_prompt
from resume.utils.validation import parse_llm_json, validate_with_schema
from tracker.models.requirement import Job, Requirement


class ResumeMatcher:
    """Evaluates how well resume skills match job requirements using LLM-based analysis.
    
    This service compares job requirement keywords against resume skill keywords to
    compute a match ratio and identify unmet requirements. It coordinates LLM calls
    to produce structured match evaluations that inform iterative resume improvements.
    """
    
    def __init__(
        self,
        client: ClaudeClient = None,
        prompt_path: str = "resume/prompts/evaluate_match.md",
    ):
        """Initialize the resume matcher.
        
        Args:
            client: LLM client for API calls. Defaults to ClaudeClient if not provided.
            prompt_path: Path to the match evaluation prompt template.
        """
        self.client = client or ClaudeClient()
        self.prompt_path = prompt_path
    
    def evaluate(
        self,
        job_id: int,
        model: str = None,
    ) -> MatchResultSchema:
        """Evaluate how well a resume's skills match a job's requirements.
        
        Args:
            job_id: The ID of the Job to evaluate requirements for.
            model: Optional LLM model identifier to use for evaluation.
            
        Returns:
            Validated MatchResultSchema instance containing unmet requirements and match ratio.
            
        Raises:
            ValueError: If LLM output is truncated or malformed.
            ValueError: If parsed JSON fails schema validation.
            Job.DoesNotExist: If job_id does not exist.
            Resume.DoesNotExist: If no resume exists for the job.
        """
        job = Job.objects.get(id=job_id)
        resume = Resume.objects.get(job=job)
        
        requirements_keywords = self._build_requirements_keywords(job)
        skill_keywords = self._build_skill_keywords(resume)
        
        prompt_template = load_prompt(self.prompt_path)
        prompt = fill_placeholders(
            prompt_template,
            {
                "REQUIREMENTS": requirements_keywords,
                "SKILLS": skill_keywords,
            }
        )
        
        response_text = self.client.generate(prompt, model=model, max_tokens=1000)
        parsed_data = parse_llm_json(response_text)
        
        validated_result = validate_with_schema(parsed_data, MatchResultSchema)
        
        return validated_result
    
    def _build_requirements_keywords(self, job: Job) -> str:
        """Build numbered list of requirement keyword groups, one per requirement.
        
        Each requirement's keywords are kept together and numbered so the LLM can
        evaluate whether each individual requirement is met by checking if any of
        its keywords appear in the skill keywords.
        
        Args:
            job: Job instance to extract requirements from.
            
        Returns:
            Formatted string with each requirement's keywords as a numbered list item.
        """
        requirements = Requirement.objects.filter(job=job).order_by('order')
        
        if not requirements.exists():
            return "No requirements specified"
        
        requirement_lines = []
        for idx, req in enumerate(requirements, start=1):
            keywords = req.keywords if isinstance(req.keywords, list) else []
            if keywords:
                keywords_str = ", ".join(keywords)
                requirement_lines.append(f"{idx}. {keywords_str}")
        
        return "\n".join(requirement_lines) if requirement_lines else "No requirements specified"
    
    def _build_skill_keywords(self, resume: Resume) -> str:
        """Build comma-separated string of all skill keywords from resume skill bullets.
        
        Args:
            resume: Resume instance to extract skill keywords from.
            
        Returns:
            Comma-separated string of unique skill keywords from all skill categories.
        """
        skill_bullets = ResumeSkillBullet.objects.filter(resume=resume)
        
        all_skills = []
        for bullet in skill_bullets:
            skills = bullet.skills_list()
            all_skills.extend(skills)
        
        unique_skills = []
        seen = set()
        for skill in all_skills:
            if skill.lower() not in seen:
                seen.add(skill.lower())
                unique_skills.append(skill)
        
        return ", ".join(unique_skills) if unique_skills else "No skills available"
