"""
budget — filters. Owner: Dev A.

`django_filters.FilterSet` classes. Compose the shared pieces in
`core/filters.py`. Nothing else belongs in this module.
"""

from django_filters import rest_framework as filters

from apps.budget.models import Expense
from core.filters import CharInFilter


class ExpenseFilterSet(filters.FilterSet):
    """`GET /trips/{id}/expenses/`. The trip itself comes from the URL, not a filter."""

    category = CharInFilter(field_name="category", lookup_expr="in")

    class Meta:
        model = Expense
        fields = ("category", "trip_stop", "is_estimated")
