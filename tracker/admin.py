from django import forms
from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Application,
    ApplicationStatus,
    ContractJob,
    Interview,
    InterviewProcessStatus,
    Job,
    LlmRequestLog,
    Requirement,
)


class InterviewInline(admin.TabularInline):
    model = Interview
    readonly_fields = [
        'stage',
        'format',
        'focus',
        'interviewer_name', 
        'interviewer_title',
        'scheduled_at',
    ]
    fields = readonly_fields + ['notes']
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
        'view_detail_link',
    ]
    list_filter = ['applied_date', 'job__role', 'job__specialization', 'status__state']
    search_fields = ['job__company']
    readonly_fields = ['job']
    inlines = [
        InterviewInline,
    ]

    def applied_date_no_time(self, obj):
        return timezone.localtime(obj.applied_date).date()
    applied_date_no_time.short_description = 'Applied Date'

    def view_detail_link(self, obj):
        url = reverse('tracker:application_detail', args=[obj.id])
        return format_html('<a href="{}">View Full Details →</a>', url)
    view_detail_link.short_description = 'Quick Actions'


class ApplicationStatusAdmin(admin.ModelAdmin):
    autocomplete_fields = ['application']
    list_display = ['application', 'state', 'status_date']


class ContractJobAdmin(admin.ModelAdmin):
    autocomplete_fields = ['job']
    list_display = ['job', 'consulting_company', 'contract_length_months']


class InterviewAdmin(admin.ModelAdmin):
    autocomplete_fields = ['application']
    list_display = ['application', 'stage', 'format', 'focus', 'scheduled_at']
    list_filter = ['stage']
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 20, 'cols': 60})},
    }

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['upcoming_interviews_url'] = reverse('tracker:upcoming_interviews')
        return super().changelist_view(request, extra_context)
    

class InterviewProcessStatusAdmin(admin.ModelAdmin):
    autocomplete_fields = ['application']
    list_display = ['application', 'outcome', 'notes']


class JobAdmin(admin.ModelAdmin):
    search_fields = ['company']
    list_display = ['company', 'listing_job_title', 'role', 'level']
    list_filter = ['role']
    ordering = ['-created_at']
    readonly_fields = ['resume']
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
admin.site.register(InterviewProcessStatus, InterviewProcessStatusAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(LlmRequestLog, LlmRequestLogAdmin)
admin.site.register(Requirement)