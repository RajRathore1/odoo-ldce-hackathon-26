"""
analytics — selectors. Owner: Dev B.

READ layer: querysets, `annotate`, `aggregate`, `select_related` /
`prefetch_related`. Never mutates anything.

`analytics` is the one app allowed to read across every other one, because it
only reads and nobody imports it (`LAYOUT.md` §5). It still does not *compute*
money: the cost totals come from `budget.services`, which owns that arithmetic.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q
from django.utils import timezone

from apps.analytics.constants import DEFAULT_PERIOD, PERIOD_DAYS, AnalyticsPeriod
from apps.budget.services import platform_cost_totals
from apps.community.models import CommunityPost, PostComment
from apps.trips.models import Trip, TripStop

ZERO = Decimal("0.00")


def resolve_period(value: str | None) -> str:
    """An unrecognised `?period=` falls back to the default rather than erroring."""
    return value if value in PERIOD_DAYS else DEFAULT_PERIOD


def period_start(period: str):
    """The cut-off for "this period", or `None` for all time."""
    days = PERIOD_DAYS.get(period)
    return None if days is None else timezone.now() - timedelta(days=days)


def _percentage(part: int, whole: int) -> float:
    """Growth as a percentage of the base it grew from. 0.0 rather than a crash."""
    return round(part / whole * 100, 1) if whole else 0.0


def overview(period: str = DEFAULT_PERIOD) -> dict:
    """
    The KPI tiles on Screen 13.

    Six queries, none of them proportional to the number of rows: four
    aggregates plus the two `platform_cost_totals` needs. Deliberately **not**
    `bulk_trip_cost_summary` over every trip — that is per-trip arithmetic, and
    on a real platform it would be a table scan per tile refresh.
    """
    user_model = get_user_model()
    since = period_start(period)

    user_filter = Q(created_at__gte=since) if since else Q()
    users = user_model.objects.aggregate(
        total=Count("pk"),
        active=Count("pk", filter=Q(is_active=True)),
        new_this_period=Count("pk", filter=user_filter),
    )

    trips = Trip.objects.aggregate(
        total=Count("pk"),
        created_this_period=Count("pk", filter=user_filter),
        public=Count("pk", filter=Q(is_public=True)),
    )
    stops = TripStop.objects.count()
    budgets = Trip.objects.aggregate(average=Avg("total_budget"))
    costs = platform_cost_totals()

    return {
        "users": {
            **users,
            # Growth against the base it grew from, not against the new total —
            # otherwise 100% growth is arithmetically impossible.
            "growth_pct": _percentage(
                users["new_this_period"], users["total"] - users["new_this_period"]
            ),
        },
        "trips": {
            **trips,
            "avg_stops_per_trip": (
                round(stops / trips["total"], 1) if trips["total"] else 0.0
            ),
        },
        "budget": {
            "avg_trip_budget": (budgets["average"] or ZERO),
            # One currency per trip and no conversion anywhere, so a
            # multi-currency platform total would be meaningless. This reports
            # the project default; revisit if trips ever mix currencies at scale.
            "currency": "INR",
            "total_planned_value": costs["grand_total"],
        },
        "content": {
            "posts": CommunityPost.objects.count(),
            "comments": PostComment.objects.count(),
        },
        "period": period,
    }


__all__ = ["AnalyticsPeriod", "overview", "resolve_period"]
