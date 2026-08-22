"""
trips — Django admin. Owner: Dev A.

Registrations for `/django-admin/`. Worth keeping current: it is how we
fix data by hand mid-demo.
"""

from django.contrib import admin

from apps.trips.models import Trip, TripActivity, TripStop


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


@admin.register(TripStop)
class TripStopAdmin(admin.ModelAdmin):
    list_display = (
        "display_title",
        "trip",
        "city",
        "start_date",
        "end_date",
        "order",
        "is_deleted",
    )
    list_filter = ("is_deleted",)
    search_fields = ("title", "city__name", "trip__name")
    list_select_related = ("trip", "city")
    autocomplete_fields = ("trip", "city")
    ordering = ("trip", "order")


@admin.register(TripActivity)
class TripActivityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "trip_stop",
        "day_date",
        "order",
        "cost",
        "currency",
        "is_deleted",
    )
    list_filter = ("is_deleted", "currency")
    search_fields = ("custom_title", "activity__name", "trip_stop__trip__name")
    list_select_related = ("trip_stop", "activity")
    autocomplete_fields = ("trip_stop", "activity")
    date_hierarchy = "day_date"
    ordering = ("trip_stop", "day_date", "order")
