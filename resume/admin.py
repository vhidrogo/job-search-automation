from django.contrib import admin
from .models import (
    ExperienceProject,
    ExperienceRole,
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


class ExperienceRoleAdmin(admin.ModelAdmin):
    inlines = [
        ExperienceProjectInline,
    ]


class ResumeTemplateAdmin(admin.ModelAdmin):
    inlines = [
        TemplateRoleConfigInline,
    ]


admin.site.register(ExperienceProject)
admin.site.register(ExperienceRole, ExperienceRoleAdmin)
admin.site.register(ResumeTemplate, ResumeTemplateAdmin)
admin.site.register(TemplateRoleConfig)
