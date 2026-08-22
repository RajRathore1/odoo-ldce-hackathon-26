"""
community — filters. Owner: Dev B.

`django_filters.FilterSet` classes. Compose the shared pieces in
`core/filters.py`. Nothing else belongs in this module.
"""

from django_filters import rest_framework as filters

from apps.community.models import CommunityPost
from core.filters import CharInFilter, SoftDeleteFilterMixin


class CommunityPostFilterSet(filters.FilterSet):
    """
    `GET /community/posts/`.

    `activity_type` reaches through the attached activity — the feed's filter
    chips are the same vocabulary as Activity Search, so "show me the adventure
    posts" works without a second field on the post itself.
    """

    activity_type = CharInFilter(field_name="activity__activity_type", lookup_expr="in")
    country = filters.NumberFilter(field_name="city__country")

    class Meta:
        model = CommunityPost
        fields = ("city", "country", "activity_type", "user", "trip")


class AdminCommunityPostFilterSet(SoftDeleteFilterMixin):
    """`GET /admin/posts/` — the moderation queue."""

    class Meta:
        model = CommunityPost
        fields = ("user", "city", "is_published", "is_flagged", "include_deleted")
