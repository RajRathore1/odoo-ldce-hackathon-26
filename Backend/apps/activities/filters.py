"""
activities — filters. Owner: Dev A (models) · Dev B (endpoints).

`django_filters.FilterSet` classes. Compose the shared pieces in
`core/filters.py`. Nothing else belongs in this module.
"""

from django_filters import rest_framework as filters

from apps.activities.models import Activity
from core.filters import CharInFilter, NumberInFilter


class ActivityFilterSet(filters.FilterSet):
    """
    `GET /activities/` — Screen 8's filter bar.

    `activity_type` and `category` take comma-separated lists because the screen
    filters with multi-select chips, not single dropdowns.
    """

    activity_type = CharInFilter(field_name="activity_type", lookup_expr="in")
    category = NumberInFilter(field_name="category", lookup_expr="in")
    country = NumberInFilter(field_name="city__country", lookup_expr="in")

    min_cost = filters.NumberFilter(field_name="cost", lookup_expr="gte")
    max_cost = filters.NumberFilter(field_name="cost", lookup_expr="lte")
    min_duration = filters.NumberFilter(field_name="duration_minutes", lookup_expr="gte")
    max_duration = filters.NumberFilter(field_name="duration_minutes", lookup_expr="lte")

    class Meta:
        model = Activity
        fields = (
            "city",
            "country",
            "category",
            "activity_type",
            "min_cost",
            "max_cost",
            "min_duration",
            "max_duration",
            "is_active",
        )
