from django.contrib import admin

from .models import (
    Application,
    ApplicationStatus,
    ContractJob,
    Interview,
    Job,
    LlmRequestLog,
    Requirement,
)


class InterviewInline(admin.TabularInline):
    model = Interview
    extra = 0


class RequirementInline(admin.TabularInline):
    model = Requirement
    readonly_fields = ['text']
    fields = ['text']
    extra = 0
    ordering = ['-relevance']


class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'applied_date_no_time',
        'job__company',
        'job__listing_job_title',
        'job__specialization',
        'status__state',
    ]
    list_filter = ['job__role', 'job__specialization', 'status__state']
    search_fields = ['job__company']
    readonly_fields = ['job']
    inlines = [
        InterviewInline,
    ]


    def applied_date_no_time(self, obj):
        return obj.applied_date.date()
    applied_date_no_time.short_description = 'Applied Date'


class ApplicationStatusAdmin(admin.ModelAdmin):
    autocomplete_fields = ['application']
    list_display = ['application', 'state', 'status_date']


class ContractJobAdmin(admin.ModelAdmin):
    autocomplete_fields = ['job']
    list_display = ['job', 'consulting_company', 'contract_length_months']


class InterviewAdmin(admin.ModelAdmin):
    autocomplete_fields = ['application']
    list_display = ['application', 'stage', 'format', 'focus', 'scheduled_at']


class JobAdmin(admin.ModelAdmin):
    search_fields = ['company']
    list_display = ['company', 'listing_job_title', 'role', 'level']
    list_filter = ['role']
    ordering = ['-created_at']
    inlines = [
        RequirementInline,
    ]

class LlmRequestLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'call_type', 'input_tokens', 'output_tokens']
    ordering = ['-timestamp']


admin.site.register(Application, ApplicationAdmin)
admin.site.register(ApplicationStatus, ApplicationStatusAdmin)
admin.site.register(ContractJob, ContractJobAdmin)
admin.site.register(Interview, InterviewAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(LlmRequestLog, LlmRequestLogAdmin)
admin.site.register(Requirement)