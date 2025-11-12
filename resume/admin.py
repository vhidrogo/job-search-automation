from django import forms
from django.contrib import admin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget

from .models import (
    ExperienceProject,
    ExperienceRole,
    Resume,
    ResumeExperienceBullet,
    ResumeExperienceRole,
    ResumeExperienceRoleBullet,
    ResumeSkillBullet,
    ResumeTemplate,
    TemplateRoleConfig,
)


class ResumeExperienceBulletInlineForm(forms.ModelForm):
    class Meta:
        model = ResumeExperienceBullet
        fields = ['experience_role', 'text', 'override_text', 'exclude']
        widgets = {
            'override_text': forms.Textarea(attrs={'rows': 2, 'cols': 50}),
        }


class ResumeExperienceRoleBulletInlineForm(forms.ModelForm):
    class Meta:
        model = ResumeExperienceRoleBullet
        fields = ['text', 'override_text', 'exclude']
        widgets = {
            'override_text': forms.Textarea(attrs={'rows': 2, 'cols': 50}),
        }


class ExperienceProjectInline(admin.TabularInline):
    model = ExperienceProject
    fields = ['short_name']
    extra = 0


class ResumeExperienceBulletInline(admin.TabularInline):
    model = ResumeExperienceBullet
    form = ResumeExperienceBulletInlineForm
    extra = 0
    ordering = ['role_order', 'role_bullet_order']
    readonly_fields = ['experience_role', 'text']
    fields = ['experience_role', 'text', 'exclude', 'override_text']


class ResumeExperienceRoleBulletInline(admin.TabularInline):
    model = ResumeExperienceRoleBullet
    form = ResumeExperienceRoleBulletInlineForm
    extra = 0
    ordering = ['order']
    readonly_fields = ['text']
    fields = ['text', 'exclude', 'override_text']


class ResumeSkillBulletInline(admin.TabularInline):
    model = ResumeSkillBullet
    extra = 0
    readonly_fields = ['category', 'skills_text']

    
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
        ResumeExperienceBulletInline,
        ResumeSkillBulletInline,
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


class ResumeExperienceRoleAdmin(admin.ModelAdmin):
    list_display = ['resume', 'experience_role']
    ordering = ['-resume__modified_at', 'order']
    inlines = [
        ResumeExperienceRoleBulletInline,
    ]


class ResumeTemplateAdmin(admin.ModelAdmin):
    inlines = [
        TemplateRoleConfigInline,
    ]


admin.site.register(ExperienceProject, ExperienceProjectAdmin)
admin.site.register(ExperienceRole, ExperienceRoleAdmin)
admin.site.register(Resume, ResumeAdmin)
admin.site.register(ResumeExperienceRole, ResumeExperienceRoleAdmin)
admin.site.register(ResumeTemplate, ResumeTemplateAdmin)
admin.site.register(TemplateRoleConfig)
