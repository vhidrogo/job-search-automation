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


class ExperienceProjectAdmin(admin.ModelAdmin):
    list_filter = ['experience_role']
    search_fields = ['short_name', 'tools']


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
admin.site.register(ResumeTemplate, ResumeTemplateAdmin)
admin.site.register(TemplateRoleConfig)
