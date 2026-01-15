import json

from resume.clients import ClaudeClient
from resume.models import ExperienceProject
from resume.utils.prompt import fill_placeholders, load_prompt
from resume.utils.validation import parse_llm_json, validate_with_schema
from tracker.models import Application, Interview, LlmRequestLog
from tracker.schemas import InterviewPrepBaseSchema, InterviewPrepSpecificSchema


class InterviewPrepGenerator:
    """
    Generates interview preparation content using LLM.
    
    Coordinates two-stage generation:
    1. Base preparation: JD formatting, company context, callback drivers, narrative
    2. Interview-specific: Predicted questions and interviewer questions per interview
    
    Uses markdown-formatted outputs for direct persistence to text fields.
    """
    
    def __init__(
        self,
        client: ClaudeClient = None,
        base_prompt_path: str = "tracker/prompts/generate_interview_prep_base.md",
        specific_prompt_path: str = "tracker/prompts/generate_interview_prep_specific.md",
    ):
        """Initialize the generator.
        
        Args:
            client: LLM client for API calls. Defaults to ClaudeClient if not provided.
            base_prompt_path: Path to base preparation prompt template.
            specific_prompt_path: Path to interview-specific prompt template.
        """
        self.client = client or ClaudeClient()
        self.base_prompt_path = base_prompt_path
        self.specific_prompt_path = specific_prompt_path
    
    def generate_base_preparation(
        self,
        application: Application,
        model: str = None,
        max_tokens: int = 4000,
    ) -> InterviewPrepBaseSchema:
        """Generate base interview preparation for an application.
        
        Args:
            application: Application to generate preparation for.
            model: Optional LLM model identifier.
            max_tokens: Maximum tokens for LLM response.
            
        Returns:
            Created InterviewPreparationBase instance.
            
        Raises:
            ValueError: If application has no associated resume.
            ValueError: If LLM output is malformed or fails validation.
        """
        resume_text = self._build_resume_text(application.job)
        
        prompt_template = load_prompt(self.base_prompt_path)
        prompt = fill_placeholders(
            prompt_template, 
            {
                "JOB_DESCRIPTION": application.job.raw_jd_text,
                "RESUME": resume_text,
            }
        )
        
        response_text = self.client.generate(
            prompt,
            call_type=LlmRequestLog.CallType.GENERATE_INTERVIEW_PREP_BASE,
            model=model,
            max_tokens=max_tokens,
        )
        parsed_data = parse_llm_json(response_text)
        validated_data = validate_with_schema(parsed_data, InterviewPrepBaseSchema)
        
        return validated_data
    
    def generate_interview_preparation(
        self,
        interview: Interview,
        model: str = None,
        max_tokens: int = 4000,
    ) -> InterviewPrepSpecificSchema:
        """Generate interview-specific preparation for an interview.
        
        Args:
            interview: Interview to generate preparation for.
            model: Optional LLM model identifier.
            max_tokens: Maximum tokens for LLM response.
            
        Returns:
            Created InterviewPreparation instance.
            
        Raises:
            ValueError: If base preparation doesn't exist.
            ValueError: If application has no associated resume.
            ValueError: If LLM output is malformed or fails validation.
        """
        if not hasattr(interview.application, "interview_prep_base"):
            raise ValueError(
                f"Base preparation must exist before generating interview-specific prep. "
                f"Run generate_base_preparation() first for application {interview.application.id}"
            )
        
        resume_text = self._build_resume_text(interview.application.job)
        prep_base = interview.application.interview_prep_base
        
        prompt_template = load_prompt(self.specific_prompt_path)
        prompt = fill_placeholders(prompt_template, {
            "JOB_DESCRIPTION": interview.application.job.raw_jd_text,
            "RESUME": resume_text,
            "RESUME_PROJECTS": self._format_projects_for_prompt(interview),
            "PRIMARY_DRIVERS": prep_base.primary_drivers,
            "INTERVIEW_STAGE": interview.get_stage_display(),
            "INTERVIEW_FOCUS": interview.get_focus_display() if interview.focus else "Not specified",
            "INTERVIEWER_TITLE": interview.interviewer_title or "Not specified",
            "PRIOR_INTERVIEW_NOTES": self._format_prior_interview_notes_for_prompt(interview),
        })
        
        response_text = self.client.generate(
            prompt,
            call_type=LlmRequestLog.CallType.GENERATE_INTERVIEW_PREP_SPECIFIC,
            model=model,
            max_tokens=max_tokens,
        )
        
        parsed_data = parse_llm_json(response_text)
        validated_data = validate_with_schema(parsed_data, InterviewPrepSpecificSchema)
        
        return validated_data
    
    def _build_resume_text(self, job) -> str:
        """
        Build structured resume text from Job's associated Resume model.
        
        Constructs a text representation including experience roles with bullets
        and skill categories. Excludes company names, dates, and locations to 
        focus on role titles and accomplishments.
        
        Args:
            job: Job instance with associated Resume.
            
        Returns:
            Structured text representation of the resume.
            
        Raises:
            ValueError: If job has no associated resume.
        """
        if not hasattr(job, "resume"):
            raise ValueError(f"Job {job.id} has no associated resume")
        
        resume = job.resume
        sections = []
        
        experience_roles = resume.roles.all()
        if experience_roles.exists():
            sections.append("EXPERIENCE\n")
            for role in experience_roles:
                sections.append(f"\n{role.title}")
                bullets = role.bullets.filter(exclude=False)
                for bullet in bullets:
                    sections.append(f"- {bullet.display_text()}")
        
        skill_categories = resume.skills_categories.filter(exclude=False)
        if skill_categories.exists():
            sections.append("\n\nSKILLS\n")
            for category in skill_categories:
                sections.append(f"{category.category}: {category.display_text()}")
        
        return "\n".join(sections)

    def _format_projects_for_prompt(self, interview) -> str:
        """
        Extract ExperienceProjects used by resume bullets for the given interview's application,
        and format them as JSON for LLM prompt context.

        Traversal:
        Interview -> Application -> Job -> Resume -> Roles -> Bullets -> ExperienceProject

        Returns:
            JSON string for RESUME_PROJECTS placeholder.
        """

        job = interview.application.job

        if not hasattr(job, "resume"):
            return "[]"

        resume = job.resume

        project_ids = (
            resume.roles
            .prefetch_related("bullets__experience_project")
            .values_list("bullets__experience_project__id", flat=True)
        )

        project_ids = [pid for pid in project_ids if pid is not None]

        if not project_ids:
            return "[]"

        projects = ExperienceProject.objects.filter(id__in=set(project_ids))

        data = [
            {
                "problem_context": p.problem_context,
                "actions": p.actions,
                "tools": p.tools,
                "outcomes": p.outcomes,
            }
            for p in projects
        ]

        return json.dumps(data, ensure_ascii=False)
    
    def _format_prior_interview_notes_for_prompt(self, interview) -> str:
        """
        Extract prior interview notes for the same application and format them as JSON.

        Structure:
        [
          {
            "stage": "Recruiter Screen",
            "focus": "Not specified",
            "date": "2026-01-10",
            "notes": "..."
          },
          ...
        ]
        """

        interviews = (
            interview.application.interviews
            .exclude(notes__isnull=True)
            .exclude(notes__exact="")
            .order_by("scheduled_at")
        )

        if not interviews.exists():
            return "[]"

        data = [
            {
                "stage": i.get_stage_display(),
                "focus": i.get_focus_display() if i.focus else "Not specified",
                "date": i.scheduled_at.strftime("%Y-%m-%d"),
                "notes": i.notes.strip(),
            }
            for i in interviews
        ]

        return json.dumps(data, ensure_ascii=False)