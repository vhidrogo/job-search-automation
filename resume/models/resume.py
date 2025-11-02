from pathlib import Path
from typing import Dict, List, Optional
from weasyprint import CSS, HTML
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.template.loader import render_to_string
from django.db import models
from django.utils.safestring import mark_safe

from .experience_role import ExperienceRole


class Resume(models.Model):
    """
    Represents a generated resume for a specific job application.

    Fields:
      - template: The ResumeTemplate used to render this resume.
      - job: The job listing this resume targets.
    """

    template = models.ForeignKey(
        "resume.ResumeTemplate",
        on_delete=models.CASCADE,
        related_name="resumes",
        help_text="Template used to generate this resume.",
    )
    job = models.OneToOneField(
        "tracker.Job",
        on_delete=models.CASCADE,
        related_name="resume",
        help_text="Job listing this resume targets.",
    )

    class Meta:
        app_label = "resume"
        indexes = [
            models.Index(fields=["template"]),
        ]

    def __str__(self) -> str:
        return f"Resume for {self.job.company} - {self.job.listing_job_title}"

    def unmet_list(self) -> Optional[list[str]]:
        """
        Returns unmet requirements as a list of strings, or None if empty.
        """
        if not self.unmet_requirements.strip():
            return None
        return [req.strip() for req in self.unmet_requirements.split(",") if req.strip()]

    def render_to_pdf(self, output_dir: str = "output/resumes") -> str:
        """
        Render this resume to a PDF file.
        
        Assembles the resume by:
        1. Fetching the template and its role configurations
        2. Querying experience bullets (filtered by exclude=False, ordered by order)
        3. Querying skill bullets
        4. Rendering HTML via Django templates with bullets and skills
        5. Converting HTML to PDF via WeasyPrint
        
        Args:
            output_dir: Directory where the PDF should be saved.
            
        Returns:
            Path to the generated PDF file.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        pdf_filename = self._generate_pdf_filename()
        pdf_path = output_path.joinpath(pdf_filename)
        
        context = self._build_template_context()
        html_string = render_to_string(self.template.template_path, context)

        css_path = Path(settings.BASE_DIR).joinpath("resume", "templates", self.template.style_path)
        
        HTML(string=html_string).write_pdf(
            str(pdf_path), 
            stylesheets=[CSS(filename=css_path)]
        )
        
        return str(pdf_path)

    def _generate_pdf_filename(self) -> str:
        company = self._sanitize_filename(self.job.company)
        title = self._sanitize_filename(self.job.listing_job_title)
        
        return f"{company}_{title}.pdf"


    def _sanitize_filename(self, text: str) -> str:
        sanitized = text.replace(" ", "_")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in ("_", "-"))

        return sanitized

    def _build_template_context(self) -> Dict[str, str]:
        """
        Build the context dictionary for template rendering.
        
        Returns:
            Dictionary with role bullet placeholders (e.g., 'first_role_bullets')
            and 'skills' HTML string.
        """
        context = {}
        
        configs = self.template.role_configs.select_related("experience_role").order_by("order")
        
        for i, config in enumerate(configs):
            bullets_html = self._render_role_bullets(config.experience_role)
            context[f"experience_bullets_{i + 1}"] = bullets_html
        
        context["skills"] = self._render_skills()
        
        return context

    def _render_role_bullets(self, experience_role: ExperienceRole) -> str:
        """
        Render HTML for experience bullets for a specific role.
        
        Args:
            experience_role: The experience role to render bullets for.
            
        Returns:
            HTML string of <li> tags.
        """
        bullets = self.experience_bullets.filter(
            experience_role=experience_role,
            exclude=False
        ).order_by("order")
        
        if not bullets.exists():
            return ""

        html = "\n ".join(f"<li>{x.display_text()}</li>" for x in bullets)

        return mark_safe(html)

    def _render_skills(self) -> str:
        """
        Render HTML for skills section.
        
        Returns:
            HTML string of skill category entries.
        """
        skill_bullets = self.skill_bullets.all()
        
        if not skill_bullets.exists():
            return ""

        html = "\n".join(
            f'<div class="skill-category"><strong>{x.category}:</strong> {x.skills_text}</div>' for x in skill_bullets
        )
        
        return mark_safe(html)
