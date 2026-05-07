"""Admin registration for the Case model — full CRUD with useful filters."""
from django.contrib import admin

from .models import Case


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("case_title", "court", "year", "violation_type", "country", "created_at")
    list_filter = ("violation_type", "year", "country", "court")
    search_fields = ("case_title", "court", "summary", "full_text", "tags")
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("case_title",)}
    date_hierarchy = "created_at"
    list_per_page = 50
    save_on_top = True
    fieldsets = (
        (
            "Identification",
            {"fields": ("case_title", "slug", "court", "country", "year")},
        ),
        (
            "Classification",
            {"fields": ("violation_type", "tags")},
        ),
        (
            "Content",
            {"fields": ("summary", "full_text")},
        ),
        (
            "Provenance",
            {
                "classes": ("collapse",),
                "fields": ("source_file", "created_at", "updated_at"),
            },
        ),
    )
