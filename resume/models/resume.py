from pathlib import Path
from html import escape
from typing import Dict
from weasyprint import CSS, HTML

from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.safestring import mark_safe

from .experience_role import ExperienceRole
from .resume_template import StylePath
from .resume_role import ResumeRole


class Resume(models.Model):
    """
    Represents a generated resume for a specific job application.

    Fields:
      - template: The ResumeTemplate used to render this resume.
      - job: The job listing this resume targets.
      - style_path: File path to the CSS stylesheet used for styling.
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
    style_path = models.CharField(
        max_length=255,
        choices=StylePath.choices,
        default=StylePath.STANDARD,
        help_text="Path to the CSS stylesheet file.",
    )

    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "resume"
        indexes = [
            models.Index(fields=["template"]),
        ]

    def __str__(self) -> str:
        return f"{self.job} - Resume"
    
    def render_to_html(self) -> str:
        """
        Render this resume to an HTML string.
        Assembles the resume by:
        1. Fetching the template and its role configurations
        2. Querying experience bullets (filtered by exclude=False, ordered by order)
        3. Querying skill categories
        4. Rendering HTML via Django templates with bullets and skills
        
        Returns:
            HTML string of the rendered resume.
        """
        context = self._build_template_context()
        html_string = render_to_string(self.template.template_path, context)
        return html_string
    
   
    def render_to_pdf(self, output_dir: str = "output/resumes") -> str:
        """
        Render this resume to a PDF file.
        Assembles the resume by:
        1. Calling render_to_html() to get the HTML string
        2. Converting HTML to PDF via WeasyPrint
        
        Args:
            output_dir: Directory where the PDF should be saved.
        
        Returns:
            Path to the generated PDF file.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        pdf_filename = self._generate_pdf_filename()
        pdf_path = output_path.joinpath(pdf_filename)
        
        html_string = self.render_to_html()
        css_path = Path(settings.BASE_DIR).joinpath("resume", "templates", self.style_path)
        
        HTML(string=html_string).write_pdf(
            str(pdf_path), 
            stylesheets=[CSS(filename=css_path)]
        )
        
        return str(pdf_path)
    
    def get_css_content(self) -> str:
        """
        Read and return the CSS content for this resume"s style.
        
        Returns:
            CSS file content as a string.
        """
        css_path = Path(settings.BASE_DIR).joinpath("resume", "templates", self.style_path)
        with open(css_path, "r") as f:
            return f.read()

    def _generate_pdf_filename(self) -> str:
        company = self._sanitize_filename(self.job.company)
        title = self._sanitize_filename(self.job.listing_job_title)
        local_modified = timezone.localtime(self.modified_at)
        date = local_modified.strftime("%Y%m%d")

        return f"{date}_{company}_{title}.pdf"


    def _sanitize_filename(self, text: str) -> str:
        sanitized = text.replace(" ", "_")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in ("_", "-", "&"))

        return sanitized

    def _build_template_context(self) -> Dict[str, str]:
        """
        Build the context dictionary for template rendering.
        
        Returns:
            Dictionary with "experience" HTML string and "skills" HTML string.
        """
        context = {}

        experience_entries = []
        for role in self.roles.all():
            entry_html = self._render_experience_entry(role)
            experience_entries.append(entry_html)
        
        context["experience"] = mark_safe("\n\n".join(experience_entries))
        context["skills"] = self._render_skills()
        
        return context

    def _render_experience_entry(self, resume_role: ResumeRole) -> str:
        """
        Render HTML for a complete experience entry.
        
        Args:
            resume_role: The resume experience role to render.
            
        Returns:
            HTML string for the complete experience entry.
        """
        header_html = self._render_experience_header(resume_role)
        subheader_html = self._render_experience_subheader(resume_role.source_role)
        bullets_html = self._render_bullets(resume_role)
        
        return f"""<div class="experience-entry">
    {header_html}
    {subheader_html}
    <ul class="experience-bullets">
        {bullets_html}
    </ul>
</div>"""

    def _render_experience_header(self, resume_role: ResumeRole) -> str:
        """
        Render HTML for the experience header (title and dates).
        
        Args:
            resume_role: The resume experience role to render.
            
        Returns:
            HTML string for the experience header with dates formatted like "May 2023".
        """
        source_role = resume_role.source_role
        start_date = source_role.start_date.strftime("%b %Y")
        end_date = source_role.end_date.strftime("%b %Y") if source_role.end_date else "Present"
        
        return f"""<div class="experience-header">
        <span class="experience-title">{resume_role.title}</span>
        <span class="experience-dates">{start_date} - {end_date}</span>
    </div>"""

    def _render_experience_subheader(self, source_role: ExperienceRole) -> str:
        """
        Render HTML for the experience subheader (company and location).
        
        Args:
            source_role: The experience role to render.
            
        Returns:
            HTML string for the experience subheader.
        """
        return f"""<div class="experience-subheader">
        <span class="experience-company">{escape(source_role.company)}</span>
        <span class="experience-location">{escape(source_role.location)}</span>
    </div>"""

    def _render_bullets(self, resume_role: ResumeRole) -> str:
        """
        Render HTML for bullets for a specific role.
        
        Args:
            resume_role: The resume experience role to render bullets for.
            
        Returns:
            HTML string of <li> tags.
        """
        bullets = resume_role.bullets.filter(exclude=False)
        if not bullets.exists():
            return ""

        html = "\n        ".join(f"<li>{escape(x.display_text())}</li>" for x in bullets)
        
        return mark_safe(html)

    def _render_skills(self) -> str:
        """
        Render HTML for skills section.
        
        Returns:
            HTML string of skills category entries.
        """
        skill_bullets = self.skills_categories.filter(exclude=False)
        
        if not skill_bullets.exists():
            return ""

        html = "\n".join(
            f"<div class='skill-category'><strong>{escape(x.category)}:</strong> {escape(x.display_text())}</div>"
            for x in skill_bullets
        )
        
        return mark_safe(html)
