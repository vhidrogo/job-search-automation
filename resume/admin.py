from django import forms
from django.contrib import admin
from django.db import models
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
        fields = ['text', 'override_text', 'exclude']
        widgets = {
            'override_text': forms.Textarea(attrs={'rows': 2, 'cols': 50}),
        }


class ExperienceProjectInline(admin.TabularInline):
    model = ExperienceProject
    fields = ['short_name']
    extra = 0


class ResumeRoleInline(admin.TabularInline):
    model = ResumeRole
    extra = 0
    ordering = ['order']
    readonly_fields = ['source_role']
    fields = ['source_role', 'title']


class ResumeRoleBulletInline(admin.TabularInline):
    model = ResumeRoleBullet
    form = ResumeRoleBulletInlineForm
    extra = 0
    ordering = ['order']
    readonly_fields = ['text']
    fields = ['text', 'exclude', 'override_text']


class ResumeSkillsCategoryInline(admin.TabularInline):
    model = ResumeSkillsCategory
    extra = 0
    readonly_fields = ['category', 'skills_text']
    fields = ['category', 'skills_text', 'exclude']

    
class TemplateRoleConfigInline(admin.TabularInline):
    model = TemplateRoleConfig
    extra = 1
    ordering = ['order']


class ExperienceProjectAdmin(admin.ModelAdmin):
    list_filter = ['experience_role']
    search_fields = ['short_name', 'tools']
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }


class ExperienceRoleAdmin(admin.ModelAdmin):
    list_display = ['company', 'title', 'start_date', 'end_date', 'location']
    ordering = ['-start_date']
    inlines = [
        ExperienceProjectInline,
    ]


class ResumeAdmin(admin.ModelAdmin):
    actions = ['render_resume_to_pdf']
    inlines = [
        ResumeRoleInline,
        ResumeSkillsCategoryInline,
    ]
    
    @admin.action(description='Render resume to PDF')
    def render_resume_to_pdf(self, request, queryset):
        for resume in queryset:
            resume.render_to_pdf()
        
        count = queryset.count()
        self.message_user(
            request,
            f'Successfully rendered {count} resume(s) to PDF.'
        )


class ResumeRoleAdmin(admin.ModelAdmin):
    list_display = ['resume', 'source_role']
    ordering = ['-resume__modified_at', 'order']
    inlines = [
        ResumeRoleBulletInline,
    ]


class ResumeTemplateAdmin(admin.ModelAdmin):
    list_filter = ['target_role', 'target_level', 'target_specialization']
    inlines = [
        TemplateRoleConfigInline,
    ]


admin.site.register(ExperienceProject, ExperienceProjectAdmin)
admin.site.register(ExperienceRole, ExperienceRoleAdmin)
admin.site.register(Resume, ResumeAdmin)
admin.site.register(ResumeRole, ResumeRoleAdmin)
admin.site.register(ResumeTemplate, ResumeTemplateAdmin)
admin.site.register(TemplateRoleConfig)
