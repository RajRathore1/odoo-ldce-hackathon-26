"""
activities — selectors. Owner: Dev A (models) · Dev B (endpoints).

READ layer: querysets, `annotate`, `aggregate`, `select_related` /
`prefetch_related`. Never mutates anything.
"""

from apps.activities.models import Activity, ActivityCategory

#: Default size of `/activities/popular/`, which is a top-N rather than a page.
POPULAR_LIMIT = 10


def activity_list():
    """
    Base queryset for Activity Search.

    Both joins are required, not optional: every row nests its category and its
    city, and the city nests its country name. Without them a 50-row page is
    150 queries (trap #9).
    """
    return Activity.objects.select_related("category", "city", "city__country")


def popular_activities(city_id: int | None = None, limit: int = POPULAR_LIMIT):
    """
    Suggestions for "what to do here".

    Reads the denormalised `popularity_score`, bumped by
    `trips.services.create_trip_activity` on every add.
    """
    queryset = activity_list().filter(is_active=True)
    if city_id is not None:
        queryset = queryset.filter(city_id=city_id)
    return queryset.order_by("-popularity_score", "-rating", "name")[:limit]


def category_list():
    """`GET /activity-categories/`. Ordered by name through `Meta`."""
    return ActivityCategory.objects.filter(is_active=True)
