from django.contrib import admin

from .models import (
    Application,
    Job,
    LlmRequestLog,
    Requirement,
)


class RequirementInline(admin.TabularInline):
    model = Requirement
    fields = ['text', 'relevance']
    extra = 0
    ordering = ['-relevance']


class JobAdmin(admin.ModelAdmin):
    list_display = ['company', 'role', 'level']
    ordering = ['-created_at']
    inlines = [
        RequirementInline,
    ]

class LlmRequestLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'call_type', 'input_tokens', 'output_tokens']
    ordering = ['-timestamp']


admin.site.register(Application)
admin.site.register(Job, JobAdmin)
admin.site.register(LlmRequestLog, LlmRequestLogAdmin)
admin.site.register(Requirement)