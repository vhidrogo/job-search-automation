from django import forms
from django.contrib import admin, messages
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Application,
    ApplicationStatus,
    ContractJob,
    Interview,
    InterviewPreparation,
    InterviewPreparationBase,
    InterviewProcessStatus,
    Job,
    LlmRequestLog,
    Requirement,
)
from .utils import generate_base_prep_for_application, generate_prep_for_interview


class InterviewInline(admin.TabularInline):
    model = Interview
    readonly_fields = [
        "stage",
        "format",
        "focus",
        "interviewer_name", 
        "interviewer_title",
        "scheduled_at",
    ]
    fields = readonly_fields + ["notes"]
    extra = 0


class RequirementInline(admin.TabularInline):
    model = Requirement
    readonly_fields = ["text"]
    fields = ["text"]
    extra = 0
    ordering = ["-relevance"]


class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "applied_date_no_time",
        "job__company",
        "job__listing_job_title",
        "job__specialization",
        "job__location",
        "status__state",
        "view_detail_link",
    ]
    list_filter = ["applied_date", "job__role", "job__specialization", "status__state"]
    search_fields = ["job__company", "job__listing_job_title", "job__external_job_id"]
    readonly_fields = ["job"]
    inlines = [
        InterviewInline,
    ]
    actions = ["generate_base_prep_action"]

    def applied_date_no_time(self, obj):
        return timezone.localtime(obj.applied_date).date()
    applied_date_no_time.short_description = "Applied Date"

    def view_detail_link(self, obj):
        url = reverse("tracker:application_detail", args=[obj.id])
        return format_html("<a href='{}'>View Full Details →</a>", url)
    view_detail_link.short_description = "Quick Actions"

    @admin.action(description="Generate base interview preparation")
    def generate_base_prep_action(modeladmin, request, queryset):
        success_count = 0
        error_count = 0
        
        for application in queryset:
            try:
                created = generate_base_prep_for_application(application.id)
                
                if created:
                    messages.success(
                        request,
                        f"{application.job.company} - {application.job.listing_job_title}: base prep created"
                    )
                    success_count += 1
                else:
                    messages.info(
                        request,
                        f"{application.job.company} - {application.job.listing_job_title}: base prep already exists"
                    )
                
            except Exception as e:
                messages.error(
                    request,
                    f"{application.job.company} - {application.job.listing_job_title}: {str(e)}"
                )
                error_count += 1
        
        if success_count:
            messages.success(request, f"Successfully generated base prep for {success_count} application(s)")
        if error_count:
            messages.error(request, f"Failed to process {error_count} application(s)")


class ApplicationStatusAdmin(admin.ModelAdmin):
    autocomplete_fields = ["application",]
    list_display = ["application", "state", "status_date"]


class ContractJobAdmin(admin.ModelAdmin):
    autocomplete_fields = ["job"]
    list_display = ["job", "consulting_company", "contract_length_months"]


class InterviewAdmin(admin.ModelAdmin):
    autocomplete_fields = ["application"]
    list_display = ["application", "stage", "format", "focus", "scheduled_at"]
    list_filter = ["stage"]
    formfield_overrides = {
        models.TextField: {"widget": forms.Textarea(attrs={"rows": 20, "cols": 60})},
    }
    actions = ["generate_interview_prep_action"]

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["upcoming_interviews_url"] = reverse("tracker:upcoming_interviews")
        return super().changelist_view(request, extra_context)
    
    def generate_interview_prep_action(modeladmin, request, queryset):
        success_count = 0
        error_count = 0
        
        for interview in queryset:
            try:
                created = generate_prep_for_interview(interview.id)
                
                if created:
                    messages.success(
                        request,
                        f"{interview.application.job.company} - {interview.get_stage_display()}: prep created"
                    )
                    success_count += 1
                else:
                    messages.info(
                        request,
                        f"{interview.application.job.company} - {interview.get_stage_display()}: prep already exists"
                    )
                
            except Exception as e:
                messages.error(
                    request,
                    f"{interview.application.job.company} - {interview.get_stage_display()}: {str(e)}"
                )
                error_count += 1
        
        if success_count:
            messages.success(request, f"Successfully generated prep for {success_count} interview(s)")
        if error_count:
            messages.error(request, f"Failed to process {error_count} interview(s)")


class InterviewPreparationAdmin(admin.ModelAdmin):
    list_display = ["interview", "stage", "created_at", "view_link"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = [
        "interview__application__job__company",
        "interview__application__job__listing_job_title"
    ]
    list_filter = ["interview__stage"]
    
    fieldsets = (
        ("Interview", {
            "fields": ("interview",)
        }),
        ("Predicted Questions", {
            "fields": ("predicted_questions",),
            "classes": ("wide",)
        }),
        ("Interviewer Questions", {
            "fields": ("interviewer_questions",),
            "classes": ("wide",)
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def stage(self, obj):
        return obj.interview.get_stage_display()
    stage.short_description = "Stage"
    stage.admin_order_field = "interview__stage"
    
    def view_link(self, obj):
        url = reverse("tracker:interview_preparation", args=[obj.interview.application.id])
        url += f"?interview_id={obj.interview.id}"
        return format_html("<a href='{}'>View Prep</a>", url)
    view_link.short_description = "View"
    

class InterviewPreparationBaseAdmin(admin.ModelAdmin):
    list_display = ["application", "created_at", "view_link"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["application__job__company", "application__job__listing_job_title"]
    
    fieldsets = (
        ("Application", {
            "fields": ("application",)
        }),
        ("Formatted Job Description", {
            "fields": ("formatted_jd",),
            "classes": ("wide",)
        }),
        ("Company Context", {
            "fields": ("company_context",),
            "classes": ("wide",)
        }),
        ("Primary Callback Drivers", {
            "fields": ("primary_drivers",),
            "classes": ("wide",)
        }),
        ("Background Narrative", {
            "fields": ("background_narrative",),
            "classes": ("wide",)
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def view_link(self, obj):
        url = reverse("tracker:interview_preparation", args=[obj.application.id])
        return format_html("<a href='{}'>View Prep</a>", url)
    view_link.short_description = "View"
    

class InterviewProcessStatusAdmin(admin.ModelAdmin):
    autocomplete_fields = ["application"]
    list_display = ["application", "outcome", "notes"]


class JobAdmin(admin.ModelAdmin):
    search_fields = ["company", "listing_job_title"]
    list_display = [
        "company",
        "listing_job_title",
        "role",
        "level",
        "location",
        "view_company_applications_link",
    ]
    list_filter = ["role"]
    ordering = ["-created_at"]
    readonly_fields = ["resume"]
    inlines = [
        RequirementInline,
    ]

    def view_company_applications_link(self, obj):
        url = reverse("tracker:company_applications", kwargs={"company_name": obj.company})
        return format_html("<a href='{}'>View Company Apps →</a>", url)
    view_company_applications_link.short_description = "Company Apps"

class LlmRequestLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "call_type", "input_tokens", "output_tokens"]
    ordering = ["-timestamp"]


admin.site.register(Application, ApplicationAdmin)
admin.site.register(ApplicationStatus, ApplicationStatusAdmin)
admin.site.register(ContractJob, ContractJobAdmin)
admin.site.register(Interview, InterviewAdmin)
admin.site.register(InterviewPreparation, InterviewPreparationAdmin)
admin.site.register(InterviewPreparationBase, InterviewPreparationBaseAdmin)
admin.site.register(InterviewProcessStatus, InterviewProcessStatusAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(LlmRequestLog, LlmRequestLogAdmin)
admin.site.register(Requirement)