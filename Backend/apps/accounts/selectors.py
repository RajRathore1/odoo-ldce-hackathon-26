"""
accounts — selectors. Owner: Dev A.

READ layer: querysets, `annotate`, `aggregate`, `select_related` /
`prefetch_related`. Never mutates anything.
"""

from decimal import Decimal

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
