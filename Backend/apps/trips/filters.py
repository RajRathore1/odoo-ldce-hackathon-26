"""
trips — filters. Owner: Dev A.

`django_filters.FilterSet` classes. Compose the shared pieces in
`core/filters.py`. Nothing else belongs in this module.
"""

from django_filters import rest_framework as filters

from apps.trips.models import Trip
from core.filters import CharInFilter, NumberInFilter


class TripFilterSet(filters.FilterSet):
    """
    `GET /trips/` — Screen 6's tabs and the "My Trips" filter bar.

    `search` and `ordering` are not declared here: they come from DRF's
    `SearchFilter` / `OrderingFilter`, which are global filter backends.
    """

    # Comma-separated so Screen 6 can ask for one tab or several:
    # `?status=ONGOING` or `?status=PLANNED,DRAFT`.
    status = CharInFilter(field_name="status", lookup_expr="in")

    start_date_after = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    start_date_before = filters.DateFilter(field_name="start_date", lookup_expr="lte")

    # "Trips containing this city / country". Method filters rather than
    # `field_name="stops__city"`, because a join does not go through the
    # soft-delete manager and a removed stop would keep matching.
    city = NumberInFilter(method="filter_city")
    country = NumberInFilter(method="filter_country")

    class Meta:
        model = Trip
        fields = (
            "status",
            "is_public",
            "start_date_after",
            "start_date_before",
            "city",
            "country",
        )

    def filter_city(self, queryset, name, value):
        return queryset.filter(stops__is_deleted=False, stops__city__in=value).distinct()

    def filter_country(self, queryset, name, value):
        return queryset.filter(
            stops__is_deleted=False, stops__city__country__in=value
        ).distinct()
