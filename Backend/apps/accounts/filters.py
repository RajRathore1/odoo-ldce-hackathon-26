"""
accounts — filters. Owner: Dev A.

`django_filters.FilterSet` classes. Compose the shared pieces in
`core/filters.py`. Nothing else belongs in this module.
"""

from django_filters import rest_framework as filters

from apps.accounts.models import User
from core.filters import CharInFilter, SoftDeleteFilterMixin


class AdminUserFilterSet(SoftDeleteFilterMixin):
    """
    `GET /admin/users/`.

    `include_deleted` comes from `SoftDeleteFilterMixin` and is the reason the
    selector reads `all_objects`: without that manager there would be nothing
    for the flag to reveal.
    """

    role = CharInFilter(field_name="role", lookup_expr="in")
    created_after = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = User
        fields = (
            "role",
            "is_active",
            "is_staff",
            "is_email_verified",
            "country",
            "city",
            "created_after",
            "created_before",
            "include_deleted",
        )
