"""
trips — Django admin. Owner: Dev A.

Registrations for `/django-admin/`. Worth keeping current: it is how we
fix data by hand mid-demo.
"""

from django.contrib import admin

from apps.trips.models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "start_date",
        "end_date",
        "status",
        "total_budget",
        "currency",
        "is_public",
        "is_deleted",
    )
    list_filter = ("status", "is_public", "is_deleted", "currency")
    search_fields = ("name", "description", "user__email")
    # Without this the changelist is one query per row for the owner's email.
    list_select_related = ("user",)
    autocomplete_fields = ("user",)
    readonly_fields = ("share_token", "views_count", "created_at", "updated_at")
    date_hierarchy = "start_date"
    ordering = ("-created_at",)
