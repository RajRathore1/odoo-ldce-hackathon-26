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

    Both counters are filtered to live rows: a join does not go through the
    soft-delete manager, so without it a deleted trip keeps counting.

    ⚠️ `distinct=True` on both is **not** cosmetic. Two `Count`s over different
    reverse relations join both tables in one query, so a user with 3 trips and
    2 posts would otherwise report 6 of each — the classic Django multiple-join
    inflation.

    `posts` is reached through the reverse accessor rather than by importing
    `community`, which `accounts` may not do (`LAYOUT.md` §5). The FK is declared
    on the other side, so the accessor exists without an import.
    """
    return (
        User.all_objects.select_related("city", "country")
        .annotate(
            trips_count=Count("trips", filter=Q(trips__is_deleted=False), distinct=True),
            posts_count=Count("posts", filter=Q(posts__is_deleted=False), distinct=True),
        )
        .order_by("-created_at")
    )
