"""
Shared filter building blocks. App-specific `FilterSet` classes live in
`apps/<app>/filters.py` and compose these.
"""

from django_filters import rest_framework as filters


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    """`?city=1,2,3` — comma-separated ids."""


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    """`?status=DRAFT,PLANNED` — comma-separated choice values."""


class RangeFilterMixin(filters.FilterSet):
    """
    Nothing to inherit yet — kept as the documented home for range helpers so
    `min_/max_` pairs end up in one place instead of being reinvented per app.

    Declare pairs on the concrete FilterSet:

        min_cost = filters.NumberFilter(field_name="cost", lookup_expr="gte")
        max_cost = filters.NumberFilter(field_name="cost", lookup_expr="lte")
    """

    class Meta:
        abstract = True


class SoftDeleteFilterMixin(filters.FilterSet):
    """
    Admin-only: let a moderator see soft-deleted rows with `?include_deleted=true`.

    Only useful on a view whose queryset comes from `Model.all_objects` — the
    default `objects` manager has already filtered them out, so there is nothing
    left for this to reveal.
    """

    include_deleted = filters.BooleanFilter(method="filter_include_deleted")

    def filter_include_deleted(self, queryset, name, value):
        return queryset if value else queryset.filter(is_deleted=False)

    class Meta:
        abstract = True
