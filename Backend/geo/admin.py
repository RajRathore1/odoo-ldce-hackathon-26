"""Admin for the geo app.

cities_light registers its own admins for Country/Region/SubRegion/City in
`cities_light.admin`. Those are kept as-is except for City, which is
re-registered so the locally-added fields show up. Subclassing their CityAdmin
retains `CityChangeList`, which transliterates the search query to match how
`search_names` is stored -- a plain ModelAdmin would silently lose that.
"""

from cities_light.admin import CityAdmin as CitiesLightCityAdmin
from django.contrib import admin

from .models import Activity, City


admin.site.unregister(City)


@admin.register(City)
class CityAdmin(CitiesLightCityAdmin):
    list_display = CitiesLightCityAdmin.list_display + ("cost_index", "popularity")
    list_filter = CitiesLightCityAdmin.list_filter + ("cost_index",)
    list_editable = ("cost_index",)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "category", "cost", "duration_minutes", "is_active"]
    list_filter = ["category", "is_active"]
    search_fields = ["name", "description", "city__name"]
    list_select_related = ["city"]
    autocomplete_fields = ["city"]
    prepopulated_fields = {"slug": ("name",)}
