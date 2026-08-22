"""
geo — Django admin. Owner: Dev A.

Registrations for `/django-admin/`. Worth keeping current: it is how we
fix data by hand mid-demo.
"""

from django.contrib import admin

from apps.geo.models import City, Country, SavedDestination


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "iso2", "region", "currency_code", "flag_emoji", "is_active")
    list_filter = ("region", "is_active")
    search_fields = ("name", "iso2", "iso3")
    ordering = ("name",)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "state",
        "country",
        "cost_index",
        "avg_daily_cost",
        "popularity_score",
        "is_active",
    )
    list_filter = ("country__region", "is_active", "country")
    search_fields = ("name", "state", "country__name")
    # Without this the changelist is one query per row for the country name.
    list_select_related = ("country",)
    autocomplete_fields = ("country",)
    ordering = ("name",)


@admin.register(SavedDestination)
class SavedDestinationAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "note", "created_at")
    search_fields = ("user__email", "city__name")
    list_select_related = ("user", "city")
    autocomplete_fields = ("user", "city")
