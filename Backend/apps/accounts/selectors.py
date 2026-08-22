"""
accounts — selectors. Owner: Dev A.

READ layer: querysets, `annotate`, `aggregate`, `select_related` /
`prefetch_related`. Never mutates anything.
"""

from decimal import Decimal

from django.db.models import Count, Q

from apps.accounts.models import User


def user_with_relations(user_id: int):
    """
    A user with `city` and `country` joined.

    `GET /users/me/` nests both, so without this the profile endpoint is three
    queries instead of one.
    """
    return (
        User.objects.select_related("city", "city__country", "country")
        .filter(pk=user_id)
        .first()
    )


def user_stats(user: User) -> dict:
    """
    The counters in the Screen 12 profile header.

    ⚠️ **Returns zeros until task A3.** Every figure here is an aggregate over
    `trips`, which does not exist yet. The shape is final and matches
    `docs/API.md` §3, so the frontend can build the header now; the real
    aggregation lands with the Trip model.

    When wiring this up in A3, do it as **one** annotated query — a naive
    implementation is five separate counts plus two distinct-joins, and this
    endpoint sits on the profile screen that every user opens.
    """
    return {
        "total_trips": 0,
        "ongoing": 0,
        "upcoming": 0,
        "completed": 0,
        "cities_visited": 0,
        "countries_visited": 0,
        "total_planned_spend": Decimal("0.00"),
        "currency": user.currency,
    }


def admin_user_queryset():
    """
    `GET /admin/users/` — the moderation table.

    Reads `all_objects`, unlike every user-facing queryset: an admin has to be
    able to see a soft-deleted account in order to restore it. The list still
    hides them by default — `core.filters.SoftDeleteFilterMixin` gives the
    moderator `?include_deleted=true` when they want them.

    `trips_count` is filtered to live trips: a join does not go through the
    soft-delete manager, so without it a deleted trip keeps counting.
    """
    return (
        User.all_objects.select_related("city", "country")
        .annotate(trips_count=Count("trips", filter=Q(trips__is_deleted=False)))
        .order_by("-created_at")
    )
