"""
budget — Django admin. Owner: Dev A.

Registrations for `/django-admin/`. Worth keeping current: it is how we
fix data by hand mid-demo.
"""

from django.contrib import admin

from apps.budget.models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "trip",
        "category",
        "amount",
        "currency",
        "incurred_on",
        "is_estimated",
        "is_deleted",
    )
    list_filter = ("category", "is_estimated", "is_deleted", "currency")
    search_fields = ("title", "notes", "trip__name")
    list_select_related = ("trip",)
    autocomplete_fields = ("trip", "trip_stop")
    date_hierarchy = "incurred_on"
