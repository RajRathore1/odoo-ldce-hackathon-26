"""
geo — selectors. Owner: models: Dev A · endpoints: Dev B.

READ layer: querysets, `annotate`, `aggregate`, `select_related` /
`prefetch_related`. Never mutates anything.
"""

from django.db.models import Count, Exists, OuterRef, Q

from apps.geo.models import City, Country, SavedDestination

#: How many activities a city detail page shows.
TOP_ACTIVITIES = 10


def city_list(user=None):
    """
    Base queryset for City Search.

    Three annotations, no per-row queries (trap #9):

    - `select_related("country")` for the nested country and the region filter
    - `activities_count`, filtered to live and active catalog rows — a join does
      not go through the soft-delete manager
    - `is_saved` as an `Exists()` subquery, so the bookmark state arrives with
      the page instead of costing a second request

    `user` may be `None` (or anonymous), in which case `is_saved` is always
    false rather than an error.
    """
    queryset = City.objects.select_related("country").annotate(
        activities_count=Count(
            "activities",
            filter=Q(activities__is_deleted=False, activities__is_active=True),
            distinct=True,
        )
    )

    if user is not None and user.is_authenticated:
        return queryset.annotate(
            is_saved=Exists(SavedDestination.objects.filter(city=OuterRef("pk"), user=user))
        )
    return queryset


def popular_cities(limit: int = TOP_ACTIVITIES, user=None):
    """
    The dashboard's "recommended destinations".

    Reads the denormalised `popularity_score` rather than counting trip stops
    live — that counter exists precisely so this is an index scan. It is bumped
    on every stop added (`trips.services.create_stop`) and can be rebuilt with
    `manage.py recalc_popularity`.
    """
    return city_list(user).filter(is_active=True).order_by("-popularity_score", "name")[:limit]


def city_top_activities(city):
    """
    The `top_activities` block of a city detail page.

    Uses the reverse accessor, so `geo` still imports nothing from `activities`
    (`LAYOUT.md` §5).
    """
    return city.activities.filter(is_active=True).order_by("-popularity_score", "-rating")[
        :TOP_ACTIVITIES
    ]


def country_list():
    """`GET /countries/`. Ordered by name through `Country.Meta`."""
    return Country.objects.all()


def saved_destinations(user):
    """`GET /users/me/saved-destinations/`, newest first."""
    return SavedDestination.objects.filter(user=user).select_related("city", "city__country")
