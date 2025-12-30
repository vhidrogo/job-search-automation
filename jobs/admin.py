from django.contrib import admin
from jobs.models import Company, WorkdayConfig, JobListing


class WorkdayConfigInline(admin.StackedInline):
    model = WorkdayConfig
    can_delete = False

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "platform", "active"]
    list_filter = ["platform", "active"]
    search_fields = ["name"]

    def get_inline_instances(self, request, obj=None):
        if obj and obj.platform == Company.Platform.WORKDAY:
            return [WorkdayConfigInline(self.model, self.admin_site)]
        return []


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "company",
        "location",
        "status",
        "is_stale",
        "last_fetched",
    ]
    list_filter = ["status"]
    search_fields = ["title", "location", "external_id"]
    readonly_fields = ["last_fetched"]

    actions = ["mark_as_interested", "mark_as_dismissed", "mark_as_applied"]

    @admin.action(description="Mark selected jobs as interested")
    def mark_as_interested(self, request, queryset):
        queryset.update(status=JobListing.Status.INTERESTED)

    @admin.action(description="Mark selected jobs as dismissed")
    def mark_as_dismissed(self, request, queryset):
        queryset.update(status=JobListing.Status.DISMISSED)

    @admin.action(description="Mark selected jobs as applied")
    def mark_as_applied(self, request, queryset):
        queryset.update(status=JobListing.Status.APPLIED)
