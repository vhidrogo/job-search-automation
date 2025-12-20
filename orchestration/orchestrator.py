import subprocess
from pypdf import PdfReader
from typing import List

from django.db import transaction

from resume.models import (
    Resume,
    ResumeRole,
    ResumeRoleBullet,
    ResumeSkillsCategory,
    ResumeTemplate,
    TargetSpecialization,
    StylePath,
)
from resume.schemas import Metadata, RequirementSchema
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
        custom_template_id: int = None,
    ):
        """Initialize orchestrator with service dependencies.
        
        Args:
            jd_parser: Service for parsing job descriptions. Defaults to JDParser().
            resume_writer: Service for generating resume content. Defaults to ResumeWriter().
            custom_template_id: Optional ID of custom ResumeTemplate to use instead of auto-selecting.
        """
        self.jd_parser = jd_parser or JDParser()
        self.resume_writer = resume_writer or ResumeWriter()
        self.custom_template_id = custom_template_id
    
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
        print(f"\n{'='*60}")
        print("Parsing job description...")

        parsed_jd = self.jd_parser.parse(jd_path)
        self._print_parsed_metadata(parsed_jd.metadata)

        template = self._get_template(parsed_jd.metadata)
        print(f"\n{'='*60}")
        print(f"Fetched template: {template}")

        job = self._persist_job_and_requirements(parsed_jd)
        print("Persisted Job")

        resume = self._create_resume(job, template)
        print("Persisted Resume")

        print(f"\n{'='*60}")
        print("Generating resume bullets...")
        
        created_counts = self._generate_and_persist_experience_bullets(resume, template, parsed_jd.requirements)

        print(f"Created {created_counts['roles_created']} roles and {created_counts['bullets_created']} bullets")

        print(f"\n{'='*60}")
        print("Generating resume skills...")

        skills = self._generate_and_persist_skills(resume, template, parsed_jd.requirements)

        print(f"Created {len(skills)} skills")

        print(f"\n{'='*60}")
        
        Application.objects.create(job=job)

        print(f"Created Application")

        print(f"\n{'='*60}")
        print("Rendering PDF...")
        
        pdf_path = self._render_pdf(resume, output_dir)
        
        print(f"Resume generated successfully!")
        print(f"PDF Location: {pdf_path}")
        print(f"\n{'='*60}")
        
        if auto_open_pdf:
            self._open_pdf(pdf_path)

    def _print_parsed_metadata(self, metadata: Metadata) -> None:
        """Print parsed job metadata in a formatted display.
        
        Args:
            metadata: Metadata instance from parsed job description.
        """
        print(f"\n{'='*60}")
        print("PARSED JOB METADATA")
        print(f"{'='*60}")
        print(f"Company:              {metadata.company}")
        print(f"Title:                {metadata.listing_job_title}")
        print(f"Role:                 {metadata.role}")
        print(f"Level:                {metadata.level}")
        print(f"Specialization:       {metadata.specialization or 'N/A'}")
        print(f"Location:             {metadata.location}")
        print(f"Work Setting:         {metadata.work_setting}")
        print(f"Min Experience:       {f'{metadata.min_experience_years} years' if metadata.min_experience_years is not None else 'N/A'}")
        print(f"External Job ID:      {metadata.external_job_id or 'N/A'}")
        
        salary_parts = []
        if metadata.min_salary is not None:
            salary_parts.append(f"${metadata.min_salary:,}")
        if metadata.max_salary is not None:
            salary_parts.append(f"${metadata.max_salary:,}")
        salary_range = " - ".join(salary_parts) if salary_parts else "N/A"
        print(f"Salary Range:         {salary_range}")
        print(f"{'='*60}")
    
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
                external_job_id=parsed_jd.metadata.external_job_id,
            )
            
            Requirement.bulk_create_from_parsed(job, parsed_jd.requirements)
        
        return job
    
    def _get_template(self, metadata: Metadata) -> ResumeTemplate:
        """Fetch matching resume template for job.
        
        If custom_template_id is set, uses that template directly.
        Otherwise, uses specialized template if job has a valid target specialization,
        or generic template for the role/level combination.
        
        Args:
            metadata: Metadata instance to find template for.
        
        Returns:
            Matching ResumeTemplate instance.
        
        Raises:
            ValueError: If no matching template exists or custom template not found.
        """
        if self.custom_template_id:
            try:
                return ResumeTemplate.objects.get(id=self.custom_template_id)
            except ResumeTemplate.DoesNotExist:
                raise ValueError(
                    f"Custom template with ID {self.custom_template_id} not found"
                )
            
        specialization = self._normalize_specialization(metadata.specialization)
        if specialization in TargetSpecialization.values:
            try:
                return ResumeTemplate.objects.get(
                    target_role=metadata.role,
                    target_level=metadata.level,
                    target_specialization=specialization,
                    is_custom=False,
                )
            except ResumeTemplate.DoesNotExist:
                raise ValueError(
                    f"No template found for role={metadata.role}, level={metadata.level}, specialization={metadata.specialization}"
                )
        else:
            try:
                return ResumeTemplate.objects.get(
                    target_role=metadata.role,
                    target_level=metadata.level,
                    target_specialization__isnull=True,
                    is_custom=False,
                )
            except ResumeTemplate.DoesNotExist:
                raise ValueError(
                    f"No template found for role={metadata.role}, level={metadata.level}"
                )
            
    def _normalize_specialization(self, specialization: str) -> str:
        if not specialization:
            return ""
        
        return "".join(c for c in specialization if c.isalpha()).lower()
    
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
            style_path=template.style_path,
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
            role = ResumeRole(
                resume=resume,
                source_role=config.experience_role,
                title=title,
                order=config.order,
            )
            roles_to_create.append(role)
            
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
    
    def _render_pdf(self, resume, output_dir) -> str:
        """Render the resume to a PDF and enforce a single-page output when possible.

        Behavior:
        - Generates a PDF using the resume's current style.
        - Counts the number of pages in the generated PDF.
        - If the PDF exceeds one page and the style is not already the densest,
          iteratively switches styles in the order: STANDARD → COMPACT → DENSE.
        - Re-renders after each style change until the PDF fits on one page or the
          densest style has been applied.
        - Returns the filesystem path to the final rendered PDF.

        Args:
            resume: Resume instance supporting `style_path`, `save()`, and `render_to_pdf()`.
            output_dir: Directory where the PDF should be written.

        Returns:
            str: Path to the final rendered PDF file.
        """
        path = resume.render_to_pdf(output_dir=output_dir)
        reader = PdfReader(path)
        page_count = len(reader.pages)

        while page_count > 1 and resume.style_path != StylePath.DENSE:
            curr_style = resume.style_path
            new_style = StylePath.COMPACT if curr_style == StylePath.STANDARD else StylePath.DENSE
            resume.style_path = new_style
            resume.save(update_fields=["style_path"])
            path = resume.render_to_pdf(output_dir=output_dir)
            
            print(
                f"Resume did not fit in one page with style = {curr_style}, "
                f"style updated to {new_style}"
            )

            reader = PdfReader(path)
            page_count = len(reader.pages)
            
        return path
    
    def _open_pdf(self, pdf_path: str) -> None:
        """Open generated PDF with system default viewer.
        
        Args:
            pdf_path: Path to PDF file.
        """
        try:
            subprocess.run(["open", pdf_path])
        except Exception as e:
            print(f"Could not auto-open PDF: {e}")
