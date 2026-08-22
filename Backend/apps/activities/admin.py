"""
activities — Django admin. Owner: Dev A.

Registrations for `/django-admin/`. Worth keeping current: it is how we
fix data by hand mid-demo.
"""

from django.contrib import admin

from apps.activities.models import Activity, ActivityCategory


@admin.register(ActivityCategory)
class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "category",
        "activity_type",
        "cost",
        "currency",
        "duration_minutes",
        "rating",
        "popularity_score",
        "is_active",
    )
    list_filter = ("activity_type", "is_active", "category")
    search_fields = ("name", "description", "city__name")
    list_select_related = ("city", "category")
    autocomplete_fields = ("city", "category")
