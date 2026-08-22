"""
trips — filters. Owner: Dev A.

`django_filters.FilterSet` classes. Compose the shared pieces in
`core/filters.py`. Nothing else belongs in this module.
"""

from django_filters import rest_framework as filters

from apps.trips.models import Trip
from core.filters import CharInFilter


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

    class Meta:
        model = Trip
        fields = ("status", "is_public", "start_date_after", "start_date_before")
