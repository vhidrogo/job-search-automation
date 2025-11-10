from django.contrib import admin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget

from .models import (
    ExperienceProject,
    ExperienceRole,
    Resume,
    ResumeTemplate,
    TemplateRoleConfig,
)


class ExperienceProjectInline(admin.TabularInline):
    model = ExperienceProject
    fields = ['short_name']
    extra = 0


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


class ResumeTemplateAdmin(admin.ModelAdmin):
    inlines = [
        TemplateRoleConfigInline,
    ]


admin.site.register(ExperienceProject, ExperienceProjectAdmin)
admin.site.register(ExperienceRole, ExperienceRoleAdmin)
admin.site.register(Resume)
admin.site.register(ResumeTemplate, ResumeTemplateAdmin)
admin.site.register(TemplateRoleConfig)
