"""Query filters backing the City Search and Activity Search screens."""

import django_filters as filters

from .models import Activity, City


class CityFilter(filters.FilterSet):
    country = filters.NumberFilter(field_name="country_id")
    country_code = filters.CharFilter(
        field_name="country__code2", lookup_expr="iexact", label="ISO alpha-2 code"
    )
    continent = filters.CharFilter(
        field_name="country__continent", lookup_expr="iexact"
    )
    region = filters.NumberFilter(field_name="region_id")
    cost_index_min = filters.NumberFilter(field_name="cost_index", lookup_expr="gte")
    cost_index_max = filters.NumberFilter(field_name="cost_index", lookup_expr="lte")

    class Meta:
        model = City
        fields = []


class ActivityFilter(filters.FilterSet):
    city = filters.NumberFilter(field_name="city_id")
    category = filters.ChoiceFilter(choices=Activity.Category.choices)
    cost_min = filters.NumberFilter(field_name="cost", lookup_expr="gte")
    cost_max = filters.NumberFilter(field_name="cost", lookup_expr="lte")
    duration_max = filters.NumberFilter(
        field_name="duration_minutes", lookup_expr="lte", label="Max duration (minutes)"
    )

    class Meta:
        model = Activity
        fields = []
