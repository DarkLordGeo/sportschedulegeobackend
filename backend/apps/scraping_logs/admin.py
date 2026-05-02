from django.contrib import admin

from .models import ScrapeRun


@admin.register(ScrapeRun)
class ScrapeRunAdmin(admin.ModelAdmin):
    list_display = (
        "source_name",
        "status",
        "started_at",
        "finished_at",
        "total_found",
        "total_created",
        "total_updated",
    )
    list_filter = ("source_name", "status")
    search_fields = ("source_name", "error_message")
    readonly_fields = (
        "source_name",
        "started_at",
        "finished_at",
        "status",
        "total_found",
        "total_created",
        "total_updated",
        "error_message",
    )
