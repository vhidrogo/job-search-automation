from pathlib import Path
from typing import Dict, List, Optional
from weasyprint import HTML
from django.core.validators import MaxValueValidator, MinValueValidator
from django.template.loader import render_to_string
from django.db import models

from .experience_role import ExperienceRole


class Resume(models.Model):
    """
    Represents a generated resume for a specific job application.

    Fields:
      - template: The ResumeTemplate used to render this resume.
      - job: The job listing this resume targets.
      - unmet_requirements: CSV string of tools/technologies not covered by this resume.
      - match_ratio: Fraction of requirements met by this resume (0.0 to 1.0).
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
    unmet_requirements = models.TextField(
        blank=True,
        default="",
        help_text="CSV string of unmatched tools/technologies (e.g., 'Go,Ruby on Rails').",
    )
    match_ratio = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Fraction of requirements met (0.0 to 1.0).",
    )

    class Meta:
        app_label = "resume"
        indexes = [
            models.Index(fields=["template"]),
        ]

    def __str__(self) -> str:
        return f"Resume for {self.job.company} — {self.job.listing_job_title} (match: {self.match_ratio:.0%})"

    def match_percentage(self) -> str:
        """
        Human-friendly match ratio as percentage string.
        """
        return f"{self.match_ratio * 100:.0f}%"

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
        
        context = self._build_template_context()
        template_name = self._get_template_name()
        html_string = render_to_string(template_name, context)
        
        pdf_filename = self._generate_pdf_filename()
        pdf_path = output_path / pdf_filename
        
        HTML(string=html_string).write_pdf(str(pdf_path))
        
        return str(pdf_path)


    def _build_template_context(self) -> Dict[str, str]:
        """
        Build the context dictionary for template rendering.
        
        Returns:
            Dictionary with role bullet placeholders (e.g., 'first_role_bullets')
            and 'skills' HTML string.
        """
        context = {}
        
        role_configs = self.template.role_configs.select_related("experience_role").order_by("order")
        
        ordinal_map = ["first", "second", "third", "fourth", "fifth", "sixth"]
        
        for idx, config in enumerate(role_configs):
            if idx >= len(ordinal_map):
                placeholder_key = f"role_{idx + 1}_bullets"
            else:
                placeholder_key = f"{ordinal_map[idx]}_role_bullets"
            
            bullets_html = self._render_role_bullets(config.experience_role)
            context[placeholder_key] = bullets_html
        
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
        
        li_tags: List[str] = []
        for bullet in bullets:
            text = bullet.display_text()
            li_tags.append(f"<li>{text}</li>")
        
        return "\n        ".join(li_tags)


    def _render_skills(self) -> str:
        """
        Render HTML for skills section.
        
        Returns:
            HTML string of skill category entries.
        """
        skill_bullets = self.skill_bullets.all()
        
        if not skill_bullets.exists():
            return ""
        
        skill_lines: List[str] = []
        for skill_bullet in skill_bullets:
            category = skill_bullet.category
            skills = skill_bullet.skills_list_display()
            skill_lines.append(f'<div class="skill-category"><strong>{category}:</strong> {skills}</div>')
        
        return "\n                    ".join(skill_lines)


    def _get_template_name(self) -> str:
        role_slug = self.job.role.lower().replace(" ", "_")
        level_slug = self.job.level.lower().replace(" ", "_")
        
        return f"html/{role_slug}_{level_slug}.html"


    def _generate_pdf_filename(self) -> str:
        company = self._sanitize_filename(self.job.company)
        title = self._sanitize_filename(self.job.listing_job_title)
        
        return f"{company}_{title}.pdf"


    def _sanitize_filename(self, text: str) -> str:
        sanitized = text.replace(" ", "_")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in ("_", "-"))

        return sanitized
