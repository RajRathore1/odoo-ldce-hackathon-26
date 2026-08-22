"""
trips — selectors. Owner: Dev A.

READ layer: querysets, `annotate`, `aggregate`, `select_related` /
`prefetch_related`. Never mutates anything.
"""

from decimal import Decimal

from django.db.models import Count, Prefetch, Q

from apps.trips.models import Trip, TripActivity, TripStop

#: What a trip's cost looks like before any cost has been recorded — and what
#: `cost_summaries_for` hands back for a trip the budget layer knows nothing
#: about. Keys match `budget.services.trip_cost_summary`.
ZERO_COST_SUMMARY = {
    "activities_cost": Decimal("0.00"),
    "expenses_cost": Decimal("0.00"),
    "grand_total": Decimal("0.00"),
    "avg_per_day": Decimal("0.00"),
    "remaining": None,
    "is_over_budget": False,
}


def trip_queryset():
    """
    Base queryset behind every trip read.

    The joins live here rather than in the view so the trip list, the trip
    detail and (later) the dashboard cannot drift into different query plans.
    Trap #9: this must stay a bounded number of queries whatever the page size,
    which is why `cities` / `stops_count` ride on one prefetch and
    `activities_count` on one annotation.

    The `filter=` on the count is not optional: a join does not go through the
    soft-delete manager, so without it a deleted stop's activities keep counting.
    """
    return (
        Trip.objects.select_related("user")
        .prefetch_related(
            Prefetch(
                "stops",
                queryset=TripStop.objects.select_related("city", "city__country").order_by(
                    "order"
                ),
            )
        )
        .annotate(
            activities_count=Count(
                "stops__activities",
                filter=Q(stops__is_deleted=False, stops__activities__is_deleted=False),
                distinct=True,
            )
        )
    )


def with_stop_activities(queryset):
    """
    Swap the list's light stop prefetch for the deep one trip detail needs.

    `prefetch_related(None)` first, because Django refuses two `Prefetch`
    objects for the same lookup — the light one has to be cleared, not added to.
    """
    return queryset.prefetch_related(None).prefetch_related(
        Prefetch(
            "stops",
            queryset=TripStop.objects.select_related("city", "city__country")
            .prefetch_related(
                Prefetch(
                    "activities",
                    queryset=TripActivity.objects.select_related("activity").order_by(
                        "day_date", "order", "id"
                    ),
                )
            )
            .order_by("order"),
        )
    )


def stop_queryset(trip):
    """
    `GET /trips/{id}/stops/`.

    The `order_by` repeats `OrderedModel.Meta.ordering` on purpose: an aggregate
    annotation sets `group_by`, which makes `QuerySet.ordered` report `False`
    even though the SQL still carries the Meta ordering — and DRF's paginator
    warns about exactly that. Being explicit is cheaper than the warning.
    """
    return (
        TripStop.objects.filter(trip=trip)
        .select_related("city", "city__country")
        .annotate(activities_count=Count("activities", filter=Q(activities__is_deleted=False)))
        .order_by("order", "id")
    )


def stop_activity_queryset(stop):
    """`GET /trips/{id}/stops/{sid}/activities/`, in itinerary order."""
    return (
        TripActivity.objects.filter(trip_stop=stop)
        .select_related("activity")
        .order_by("day_date", "order", "id")
    )


def trip_activity_queryset():
    """
    Base queryset for the flat `/trip-activities/{id}/` routes.

    Not owner-scoped here — `OwnerQuerysetMixin` does that with
    `owner_field = "trip_stop__trip__user"`.
    """
    return TripActivity.objects.select_related("activity", "trip_stop", "trip_stop__trip")


def cost_summaries_for(trip_ids) -> dict[int, dict]:
    """
    `{trip_id: cost summary}` for a whole page, in one query.

    ⚠️ **Returns zeros until task A6.** `estimated_cost` and `is_over_budget`
    come from `budget.services.bulk_trip_cost_summary`, which needs the
    `Expense` table. This is the single call site, so landing A6 is a change to
    this function's body and nothing else — the serializer already renders
    whatever it returns.
    """
    return dict.fromkeys(trip_ids, ZERO_COST_SUMMARY)
