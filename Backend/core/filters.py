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

    ⚠️ The exclusion lives in `filter_queryset`, not in the filter method,
    because **django-filter does not call a method filter when its parameter is
    absent**. With the rule in the method, a request that simply omits
    `include_deleted` got the raw `all_objects` queryset — every soft-deleted row
    on an endpoint whose whole purpose is to hide them by default.
    """

    include_deleted = filters.BooleanFilter(
        method="filter_include_deleted",
        label="Include soft-deleted rows",
    )

    def filter_include_deleted(self, queryset, name, value):
        """
        Deliberately a pass-through.

        `django_filters` needs a callable to bind the parameter and put it in
        `form.cleaned_data`, but the decision has to be made where the *absent*
        case is also visible — see `filter_queryset` below.
        """
        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        if not self.form.cleaned_data.get("include_deleted"):
            queryset = queryset.filter(is_deleted=False)
        return queryset

    class Meta:
        abstract = True
