from django import forms
from django.contrib import admin, messages
from django.db import models
from django.shortcuts import redirect
from django.urls import path, reverse
from django_json_widget.widgets import JSONEditorWidget

from .models import (
    ExperienceProject,
    ExperienceRole,
    Resume,
    ResumeRole,
    ResumeRole,
    ResumeRoleBullet,
    ResumeSkillsCategory,
    ResumeTemplate,
    TemplateRoleConfig,
)


class ResumeRoleBulletInlineForm(forms.ModelForm):
    class Meta:
        model = ResumeRoleBullet
        fields = ["text", "override_text", "exclude"]
        widgets = {
            "override_text": forms.Textarea(attrs={"rows": 2, "cols": 50}),
        }


class ResumeSkillsCategoryInlineForm(forms.ModelForm):
    class Meta:
        model = ResumeSkillsCategory
        fields = ["category", "skills_text", "override_text", "exclude"]
        widgets = {
            "override_text": forms.Textarea(attrs={"rows": 2, "cols": 50}),
        }


class ExperienceProjectInline(admin.TabularInline):
    model = ExperienceProject
    fields = ["short_name"]
    extra = 0


class ResumeRoleInline(admin.TabularInline):
    model = ResumeRole
    extra = 0
    ordering = ["order"]
    readonly_fields = ["source_role"]
    fields = ["source_role", "title"]


class ResumeRoleBulletInline(admin.TabularInline):
    model = ResumeRoleBullet
    form = ResumeRoleBulletInlineForm
    extra = 0
    ordering = ["order"]
    readonly_fields = ["text"]
    fields = ["text", "experience_project", "exclude", "override_text"]
    autocomplete_fields = ["experience_project"]


class ResumeSkillsCategoryInline(admin.TabularInline):
    model = ResumeSkillsCategory
    form = ResumeSkillsCategoryInlineForm
    extra = 0
    readonly_fields = ["category", "skills_text"]
    fields = ["category", "skills_text", "override_text", "exclude"]

    
class TemplateRoleConfigInline(admin.TabularInline):
    model = TemplateRoleConfig
    extra = 1
    ordering = ["order"]


class ExperienceProjectAdmin(admin.ModelAdmin):
    list_display = ["short_name", "experience_role"]
    list_filter = ["experience_role"]
    search_fields = ["short_name", "tools"]
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }


class ExperienceRoleAdmin(admin.ModelAdmin):
    list_display = ["company", "title", "start_date", "end_date", "location"]
    ordering = ["-start_date"]
    inlines = [
        ExperienceProjectInline,
    ]


class ResumeAdmin(admin.ModelAdmin):
    search_fields = ["job__company"]
    actions = ["render_resume_to_pdf"]
    change_form_template = "admin/resume/resume/change_form.html"
    inlines = [
        ResumeRoleInline,
        ResumeSkillsCategoryInline,
    ]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/render-pdf/',
                self.admin_site.admin_view(self.render_pdf_view),
                name='resume_resume_render_pdf',
            ),
        ]
        return custom_urls + urls
    
    def render_pdf_view(self, request, object_id):
        resume = self.get_object(request, object_id)
        if resume is None:
            self.message_user(request, "Resume not found.", level=messages.ERROR)
            return redirect('admin:resume_resume_changelist')
        
        try:
            pdf_path = resume.render_to_pdf()
            self.message_user(
                request,
                f"Successfully rendered resume to PDF: {pdf_path}",
                level=messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request,
                f"Error rendering PDF: {str(e)}",
                level=messages.ERROR
            )
        
        return redirect('admin:resume_resume_change', object_id=object_id)
    
    @admin.action(description="Render resume to PDF")
    def render_resume_to_pdf(self, request, queryset):
        for resume in queryset:
            resume.render_to_pdf()
        
        count = queryset.count()
        self.message_user(
            request,
            f"Successfully rendered {count} resume(s) to PDF."
        )


class ResumeRoleAdmin(admin.ModelAdmin):
    list_display = ["resume", "source_role"]
    ordering = ["-resume__modified_at", "order"]
    search_fields = ["resume__job__company"]
    inlines = [
        ResumeRoleBulletInline,
    ]


class ResumeTemplateAdmin(admin.ModelAdmin):
    list_display = ["id", "target_role", "target_level", "target_specialization", "description"]
    list_filter = ["target_role", "target_level", "target_specialization", "is_custom"]
    readonly_fields = ["id"]
    inlines = [
        TemplateRoleConfigInline,
    ]


admin.site.register(ExperienceProject, ExperienceProjectAdmin)
admin.site.register(ExperienceRole, ExperienceRoleAdmin)
admin.site.register(Resume, ResumeAdmin)
admin.site.register(ResumeRole, ResumeRoleAdmin)
admin.site.register(ResumeTemplate, ResumeTemplateAdmin)
admin.site.register(TemplateRoleConfig)
