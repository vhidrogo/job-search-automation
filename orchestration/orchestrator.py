import subprocess
from typing import Dict, List

from django.db import transaction

from resume.models import (
    Resume,
    ResumeExperienceBullet,
    ResumeSkillBullet,
    ResumeTemplate,
)
from resume.services.jd_parser import JDParser
from resume.services.resume_matcher import ResumeMatcher
from resume.services.resume_writer import ResumeWriter
from tracker.models import Job, Requirement


class Orchestrator:
    """Orchestrates end-to-end resume generation workflow.
    
    This class coordinates the full automation pipeline:
    1. Parse job description to extract metadata and requirements
    2. Persist job and requirement records
    3. Generate experience bullets for each configured role
    4. Generate skill bullets based on experience content
    5. Evaluate match quality and update resume metadata
    6. Render initial PDF for user review
    
    The orchestrator enables iterative improvement by exposing match scores
    and unmet requirements, allowing users to refine resume content before
    final submission.
    """
    
    def __init__(
        self,
        jd_parser: JDParser = None,
        resume_writer: ResumeWriter = None,
        resume_matcher: ResumeMatcher = None,
    ):
        """Initialize orchestrator with service dependencies.
        
        Args:
            jd_parser: Service for parsing job descriptions. Defaults to JDParser().
            resume_writer: Service for generating resume content. Defaults to ResumeWriter().
            resume_matcher: Service for evaluating match quality. Defaults to ResumeMatcher().
        """
        self.jd_parser = jd_parser or JDParser()
        self.resume_writer = resume_writer or ResumeWriter()
        self.resume_matcher = resume_matcher or ResumeMatcher()
    
    def run(
        self,
        jd_path: str,
        output_dir: str = "output/resumes",
        auto_open_pdf: bool = True,
    ) -> Resume:
        """Execute end-to-end resume generation workflow.
        
        Args:
            jd_path: Path to job description file.
            jd_text: Raw job description text.
            output_dir: Directory for PDF output.
            auto_open_pdf: Whether to automatically open the generated PDF.
            
        Returns:
            Generated Resume instance with populated bullets and match evaluation.
            
        Raises:
            ValueError: If neither jd_source nor jd_text is provided.
            ValueError: If no matching template exists for the job role and level.
        """
        parsed_jd = self.jd_parser.parse(jd_path)
        
        job = self._persist_job_and_requirements(parsed_jd)
        template = self._get_template(job)
        resume = self._create_resume(job, template)
        print('resume:', resume)
        # TODO: refactor ResumeWriter to take in list of pydantic schemas (for requirements) and access the attributes accordingly (currently using dict access patterns)
        # TODO: mock ResumeWriter before continuing, but check if _prepare_requirements_data is needed (the plan was to use the one from parsed_jd)
        # self._generate_and_persist_bullets(resume, job, template)
        
        # job.evaluate_and_update_match()
        
        # pdf_path = resume.render_to_pdf(output_dir=output_dir)
        
        # print(f"\n{'='*60}")
        # print(f"Resume generated successfully!")
        # print(f"{'='*60}")
        # print(f"Company: {job.company}")
        # print(f"Role: {job.listing_job_title}")
        # print(f"Match Score: {resume.match_percentage()}")
        # if resume.unmet_list():
        #     print(f"Unmet Requirements: {', '.join(resume.unmet_list())}")
        # print(f"PDF Location: {pdf_path}")
        # print(f"{'='*60}\n")
        
        # if auto_open_pdf:
        #     self._open_pdf(pdf_path)
    
    def _persist_job_and_requirements(self, parsed_jd) -> Job:
        """Persist job metadata and requirements to database.
        
        Args:
            parsed_jd: Validated JDModel instance from parser.
            
        Returns:
            Created Job instance.
        """
        with transaction.atomic():
            job = Job.objects.create(
                company=parsed_jd.metadata.company,
                listing_job_title=parsed_jd.metadata.listing_job_title,
                role=parsed_jd.metadata.role,
                specialization=parsed_jd.metadata.specialization,
                level=parsed_jd.metadata.level,
                location=parsed_jd.metadata.location,
                work_setting=parsed_jd.metadata.work_setting,
                min_experience_years=parsed_jd.metadata.min_experience_years,
                min_salary=parsed_jd.metadata.min_salary,
                max_salary=parsed_jd.metadata.max_salary,
            )
            
            Requirement.bulk_create_from_parsed(job, parsed_jd.requirements)
        
        return job
    
    def _get_template(self, job: Job) -> ResumeTemplate:
        """Fetch matching resume template for job.
        
        Args:
            job: Job instance to find template for.
            
        Returns:
            Matching ResumeTemplate instance.
            
        Raises:
            ValueError: If no matching template exists.
        """
        try:
            template = ResumeTemplate.objects.get(
                target_role=job.role,
                target_level=job.level,
            )
            return template
        except ResumeTemplate.DoesNotExist:
            raise ValueError(
                f"No template found for role={job.role}, level={job.level}"
            )
    
    def _create_resume(self, job: Job, template: ResumeTemplate) -> Resume:
        """Create initial resume record.
        
        Args:
            job: Job instance to create resume for.
            template: Template to use for resume.
            
        Returns:
            Created Resume instance.
        """
        resume = Resume.objects.create(
            job=job,
            template=template,
        )
        return resume
    
    def _generate_and_persist_bullets(
        self,
        resume: Resume,
        job: Job,
        template: ResumeTemplate,
    ) -> None:
        """Generate and persist experience and skill bullets.
        
        Args:
            resume: Resume instance to populate.
            job: Job instance with requirements.
            template: Template with role configurations.
        """
        requirements_data = self._prepare_requirements_data(job)
        
        self._generate_experience_bullets(resume, template, requirements_data)
        
        self._generate_skill_bullets(resume, requirements_data, job.role)
    
    def _prepare_requirements_data(self, job: Job) -> List[Dict]:
        """Prepare requirements data sorted by relevance.
        
        Args:
            job: Job instance to extract requirements from.
            
        Returns:
            List of requirement dictionaries sorted by relevance (highest first).
        """
        requirements = Requirement.objects.filter(job=job).order_by(
            "-relevance", "order"
        )
        
        requirements_data = []
        for req in requirements:
            requirements_data.append({
                "text": req.text,
                "keywords": req.keywords,
                "relevance": req.relevance,
            })
        
        return requirements_data
    
    def _generate_experience_bullets(
        self,
        resume: Resume,
        template: ResumeTemplate,
        requirements_data: List[Dict],
    ) -> None:
        """Generate and persist experience bullets for all configured roles.
        
        Args:
            resume: Resume instance to populate.
            template: Template with role configurations.
            requirements_data: Sorted list of requirement dictionaries.
        """
        role_configs = template.role_configs.select_related(
            "experience_role"
        ).order_by("order")
        
        bullets_to_create = []
        
        for config in role_configs:
            bullet_list = self.resume_writer.generate_experience_bullets(
                experience_role=config.experience_role,
                requirements=requirements_data,
                target_role=template.target_role,
                max_bullet_count=config.max_bullet_count,
            )
            
            for bullet in bullet_list.bullets:
                bullets_to_create.append(
                    ResumeExperienceBullet(
                        resume=resume,
                        experience_role=config.experience_role,
                        order=bullet.order,
                        text=bullet.text,
                    )
                )
        
        ResumeExperienceBullet.objects.bulk_create(bullets_to_create)
    
    def _generate_skill_bullets(
        self,
        resume: Resume,
        requirements_data: List[Dict],
        target_role: str,
    ) -> None:
        """Generate and persist skill bullets.
        
        Args:
            resume: Resume instance to populate.
            requirements_data: Sorted list of requirement dictionaries.
            target_role: Target job role string.
        """
        skill_bullet_list = self.resume_writer.generate_skill_bullets(
            resume=resume,
            requirements=requirements_data,
            target_role=target_role,
            max_category_count=6,
        )
        
        skills_to_create = []
        for skill_category in skill_bullet_list.skill_categories:
            skills_to_create.append(
                ResumeSkillBullet(
                    resume=resume,
                    category=skill_category.category,
                    skills_text=skill_category.skills_text,
                )
            )
        
        ResumeSkillBullet.objects.bulk_create(skills_to_create)
    
    def _open_pdf(self, pdf_path: str) -> None:
        """Open generated PDF with system default viewer.
        
        Args:
            pdf_path: Path to PDF file.
        """
        try:
            subprocess.run(["open", pdf_path])
        except Exception as e:
            print(f"Could not auto-open PDF: {e}")
