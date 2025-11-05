from django.contrib import admin
from .models import ExperienceRole, ResumeTemplate, TemplateRoleConfig


class TemplateRoleConfigInline(admin.TabularInline):
    model = TemplateRoleConfig


class ResumeTemplateAdmin(admin.ModelAdmin):
    inlines = [
        TemplateRoleConfigInline,
    ]


admin.site.register(ExperienceRole)
admin.site.register(ResumeTemplate, ResumeTemplateAdmin)
admin.site.register(TemplateRoleConfig)
