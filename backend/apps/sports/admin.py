from django.contrib import admin

from .models import Organization, Sport


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sport", "website_url")
    list_filter = ("sport",)
    search_fields = ("name", "slug", "website_url")
    prepopulated_fields = {"slug": ("name",)}
