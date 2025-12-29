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
