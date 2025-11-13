from django.contrib import admin

from .models import (
    Application,
    Job,
    LlmRequestLog,
    Requirement,
)


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['applied_date_no_time', 'job__company', 'job__role', 'job__level', 'job__specialization']
    list_filter = ['job__role', 'job__specialization']

    def applied_date_no_time(self, obj):
        return obj.applied_date.date()
    applied_date_no_time.short_description = 'Applied Date'


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


admin.site.register(Application, ApplicationAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(LlmRequestLog, LlmRequestLogAdmin)
admin.site.register(Requirement)