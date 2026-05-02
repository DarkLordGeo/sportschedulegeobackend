from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "sport",
        "organization",
        "country",
        "start_date",
        "end_date",
        "status",
    )
    list_filter = ("sport", "organization", "country", "status")
    search_fields = ("title", "location", "country", "city", "source_url", "external_id")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
