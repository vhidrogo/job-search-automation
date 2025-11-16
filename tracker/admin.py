from django.contrib import admin

from .models import (
    Application,
    ApplicationStatus,
    Job,
    LlmRequestLog,
    Requirement,
)


class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'applied_date_no_time',
        'job__company',
        'job__listing_job_title',
        'job__role',
        'job__level',
        'job__specialization',
        'status__state',
    ]
    list_filter = ['job__role', 'job__specialization', 'status__state']
    search_fields = ['job__company']


    def applied_date_no_time(self, obj):
        return obj.applied_date.date()
    applied_date_no_time.short_description = 'Applied Date'


class ApplicationStatusAdmin(admin.ModelAdmin):
    autocomplete_fields = ['application']
    list_display = ['application', 'state', 'status_date']


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
admin.site.register(ApplicationStatus, ApplicationStatusAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(LlmRequestLog, LlmRequestLogAdmin)
admin.site.register(Requirement)