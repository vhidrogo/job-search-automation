import subprocess
from typing import List

from django.db import transaction

from resume.models import (
    Resume,
    ResumeRole,
    ResumeRoleBullet,
    ResumeSkillsCategory,
    ResumeTemplate,
    TargetSpecialization,
)
from resume.schemas import RequirementSchema
from resume.services import JDParser, ResumeWriter
from tracker.models import Application, Job, Requirement


class Orchestrator:
    """Orchestrates end-to-end resume generation workflow.
    
    This class coordinates the full automation pipeline:
    1. Parse job description to extract metadata and requirements
    2. Persist job and requirement records
    3. Generate experience bullets for each configured role
    4. Generate skill bullets based on experience content
    5. Render initial PDF for user review
    
    """
    
    def __init__(
        self,
        jd_parser: JDParser = None,
        resume_writer: ResumeWriter = None,
    ):
        """Initialize orchestrator with service dependencies.
        
        Args:
            jd_parser: Service for parsing job descriptions. Defaults to JDParser().
            resume_writer: Service for generating resume content. Defaults to ResumeWriter().
        """
        self.jd_parser = jd_parser or JDParser()
        self.resume_writer = resume_writer or ResumeWriter()
    
    def run(
        self,
        jd_path: str,
        output_dir: str = "output/resumes",
        auto_open_pdf: bool = True,
    ) -> Resume:
        """Execute end-to-end resume generation workflow.
        
        Args:
            jd_path: Path to job description file.
            output_dir: Directory for PDF output.
            auto_open_pdf: Whether to automatically open the generated PDF.
            
        Returns:
            Generated Resume instance with populated bullets and skills.
            
        Raises:
            ValueError: If neither jd_source nor jd_text is provided.
            ValueError: If no matching template exists for the job role and level.
        """
        parsed_jd = self.jd_parser.parse(jd_path)
        print(f"\n{'='*60}")
        print(f"Parsed job description for {parsed_jd.metadata.company} - {parsed_jd.metadata.listing_job_title}")

        job = self._persist_job_and_requirements(parsed_jd)
        template = self._get_template(job)
        resume = self._create_resume(job, template)
        print("Persisted Job and Resume")
        
        created_counts = self._generate_and_persist_experience_bullets(resume, template, parsed_jd.requirements)
        print(f"\n{'='*60}")
        print(f"Created {created_counts['roles_created']} resume roles and {created_counts['bullets_created']} bullets")

        skills = self._generate_and_persist_skills(resume, template, parsed_jd.requirements)
        print(f"Created {len(skills)} resume skills")
        
        pdf_path = resume.render_to_pdf(output_dir=output_dir)
        print(f"\n{'='*60}")
        print(f"Resume generated successfully!")
        print(f"PDF Location: {pdf_path}")

        Application.objects.create(job=job)
        print(f"\n{'='*60}")
        print(f"Created Application")
        
        if auto_open_pdf:
            self._open_pdf(pdf_path)
    
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
        
        Uses specialized template if job has a valid target specialization,
        otherwise uses generic template for the role/level combination.
        
        Args:
            job: Job instance to find template for.
        
        Returns:
            Matching ResumeTemplate instance.
        
        Raises:
            ValueError: If no matching template exists for the job's requirements.
        """
        if job.specialization and job.specialization in TargetSpecialization.values:
            try:
                return ResumeTemplate.objects.get(
                    target_role=job.role,
                    target_level=job.level,
                    target_specialization=job.specialization,
                )
            except ResumeTemplate.DoesNotExist:
                raise ValueError(
                    f"No template found for role={job.role}, level={job.level}, specialization={job.specialization}"
                )
        else:
            try:
                return ResumeTemplate.objects.get(
                    target_role=job.role,
                    target_level=job.level,
                    target_specialization__isnull=True,
                )
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
    
    def _generate_and_persist_experience_bullets(
        self,
        resume: Resume,
        template: ResumeTemplate,
        requirements: List[RequirementSchema],
    ) -> None:
        """Generate and persist experience bullets for all configured roles.
        
        Args:
            resume: Resume instance to populate.
            template: Template with role configurations.
            requirements: List of RequirementSchema objects.
        """
        role_configs = template.role_configs.select_related(
            "experience_role"
        ).order_by("order")
        
        roles_to_create = []
        bullets_to_create = []

        for config in role_configs:
            bullet_list = self.resume_writer.generate_experience_bullets(
                experience_role=config.experience_role,
                requirements=requirements,
                target_role=template.target_role,
                max_bullet_count=config.max_bullet_count,
            )
            title = config.title_override if config.title_override else config.experience_role.title
            role = ResumeRole.objects.create(
                resume=resume,
                source_role=config.experience_role,
                title=title,
                order=config.order,
            )
            
            for bullet in bullet_list.bullets:
                bullets_to_create.append(
                    ResumeRoleBullet(
                        resume_role=role,
                        order=bullet.order,
                        text=bullet.text,
                    )
                )
        
        created_roles = ResumeRole.objects.bulk_create(roles_to_create)
        created_bullets = ResumeRoleBullet.objects.bulk_create(bullets_to_create)
    
        return {"roles_created": len(created_roles), "bullets_created": len(created_bullets)}

    
    def _generate_and_persist_skills(
        self,
        resume: Resume,
        template: ResumeTemplate,
        requirements: List[RequirementSchema],
    ) -> None:
        """Generate and persist skills categories.
        
        Args:
            resume: Resume instance to populate.
            requirements: List of RequirementSchema objects.
            template: Template with role configurations.
        """
        skills_list = self.resume_writer.generate_skills(template, requirements)
        
        skills_to_create = []
        for item in skills_list.skills_categories:
            skills_to_create.append(
                ResumeSkillsCategory(
                    resume=resume,
                    order=item.order,
                    category=item.category,
                    skills_text=item.skills,
                )
            )
        
        created = ResumeSkillsCategory.objects.bulk_create(skills_to_create)

        return created
    
    def _open_pdf(self, pdf_path: str) -> None:
        """Open generated PDF with system default viewer.
        
        Args:
            pdf_path: Path to PDF file.
        """
        try:
            subprocess.run(["open", pdf_path])
        except Exception as e:
            print(f"Could not auto-open PDF: {e}")
