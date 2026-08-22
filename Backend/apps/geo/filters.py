"""
geo — filters. Owner: models: Dev A · endpoints: Dev B.

`django_filters.FilterSet` classes. Compose the shared pieces in
`core/filters.py`. Nothing else belongs in this module.
"""

from django_filters import rest_framework as filters

from apps.geo.models import City, Country
from core.filters import SoftDeleteFilterMixin


class CityFilterSet(filters.FilterSet):
    """
    `GET /cities/` — Screen 7's filter bar.

    `search` and `ordering` come from the global DRF backends, not from here.
    """

    # The region lives on the country, not the city — one join, one filter.
    region = filters.CharFilter(field_name="country__region", lookup_expr="iexact")

    min_cost_index = filters.NumberFilter(field_name="cost_index", lookup_expr="gte")
    max_cost_index = filters.NumberFilter(field_name="cost_index", lookup_expr="lte")

    class Meta:
        model = City
        fields = ("country", "region", "min_cost_index", "max_cost_index", "is_active")


class CountryFilterSet(filters.FilterSet):
    """`GET /countries/` — `?region=` for the registration dropdown."""

    region = filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Country
        fields = ("region", "is_active")


class AdminCountryFilterSet(SoftDeleteFilterMixin):
    """`GET /admin/countries/` — adds `?include_deleted=`."""

    region = filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Country
        fields = ("region", "is_active", "include_deleted")


class AdminCityFilterSet(SoftDeleteFilterMixin):
    """`GET /admin/cities/` — adds `?include_deleted=`."""

    region = filters.CharFilter(field_name="country__region", lookup_expr="iexact")

    class Meta:
        model = City
        fields = ("country", "region", "is_active", "include_deleted")
