"""
trips — selectors. Owner: Dev A.

READ layer: querysets, `annotate`, `aggregate`, `select_related` /
`prefetch_related`. Never mutates anything.
"""

from collections import defaultdict
from decimal import Decimal

from django.db.models import Count, Prefetch, Q
from django.db.models.functions import TruncMonth

from apps.trips.constants import TripStatus
from apps.trips.models import Trip, TripActivity, TripStop
from core.utils import daterange

ZERO = Decimal("0.00")

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


def itinerary_for_trip(trip) -> list[dict]:
    """
    One row per date in the trip range — **including the empty ones**.

    The frontend renders a placeholder for a day with nothing on it and does not
    compute gaps itself (trap #6), so a ten-day trip always returns ten rows.
    `stop` is `None` on days no stop covers.

    Two queries whatever the size of the itinerary: the stops, and the
    activities. The bucketing is Python over rows already in memory.

    Where two stops overlap a date, the **earlier `order`** wins. Overlap is
    legal — a travel day can belong to the stop you are leaving — and the
    itinerary has one column, so it has to pick one.
    """
    stops = list(
        TripStop.objects.filter(trip=trip)
        .select_related("city", "city__country")
        .order_by("order")
    )
    activities = list(
        TripActivity.objects.filter(trip_stop__trip=trip, trip_stop__is_deleted=False)
        .select_related("activity")
        .order_by("day_date", "order", "id")
    )

    activities_by_day = defaultdict(list)
    for activity in activities:
        activities_by_day[activity.day_date].append(activity)

    stop_by_day: dict = {}
    for stop in stops:
        for day in daterange(stop.start_date, stop.end_date):
            stop_by_day.setdefault(day, stop)

    days = []
    for day_number, day in enumerate(daterange(trip.start_date, trip.end_date), start=1):
        on_this_day = activities_by_day.get(day, [])
        days.append(
            {
                "date": day,
                "day_number": day_number,
                "stop": stop_by_day.get(day),
                "activities": on_this_day,
                # Activities only. The budget endpoint's `by_day` is a different
                # number — it adds that day's one-off expenses on top.
                "day_total_cost": sum((item.cost for item in on_this_day), ZERO),
            }
        )
    return days


def group_itinerary_by_stop(days: list[dict]) -> list[dict]:
    """
    Regroup `itinerary_for_trip` output under its stops, for `?view=stop`.

    Pure — no queries. Groups keep the order the stops are in, and days that no
    stop covers land in a trailing group with `stop: None`, so no day is ever
    dropped from the response just because it changed shape.
    """
    groups: dict = {}
    for day in days:
        stop = day["stop"]
        key = stop.pk if stop else None
        group = groups.setdefault(key, {"stop": stop, "days": [], "stop_total_cost": ZERO})
        group["days"].append(day)
        group["stop_total_cost"] += day["day_total_cost"]

    covered = [group for key, group in groups.items() if key is not None]
    uncovered = [group for key, group in groups.items() if key is None]
    covered.sort(key=lambda group: group["stop"].order)
    return covered + uncovered


def cost_summaries_for(trip_ids) -> dict[int, dict]:
    """
    `{trip_id: cost summary}` for a whole page, in three queries.

    The import is **deferred into the function body** on purpose: `budget`
    imports `trips`, so a module-level import here would close the cycle.
    Calling it from inside keeps the dependency one-directional at import time
    and documents the direction (`LAYOUT.md` §5).

    Falls back to zeros for a trip the budget layer returned nothing for, so a
    caller never has to handle a missing key.
    """
    from apps.budget.services import bulk_trip_cost_summary  # deferred: budget → trips

    summaries = bulk_trip_cost_summary(trip_ids)
    return {trip_id: summaries.get(trip_id, ZERO_COST_SUMMARY) for trip_id in trip_ids}


#: Display order for `?group_by=status`. Not the declaration order and not
#: alphabetical: it is the order Screen 3's chips read in, most current first.
STATUS_ORDER = (
    TripStatus.ONGOING,
    TripStatus.PLANNED,
    TripStatus.DRAFT,
    TripStatus.COMPLETED,
    TripStatus.CANCELLED,
)

GROUP_BY_CHOICES = ("status", "month", "country")


def trip_groups(queryset, group_by: str) -> list[dict]:
    """
    Counts for the "Group by" control, as `[{key, label, count}]`.

    Computed over the **whole filtered queryset**, not the current page: a chip
    reading "Completed (5)" has to mean five trips, not five on this page.

    Empty groups are omitted — these are chips, and a chip for a status the user
    has never used is noise.

    ⚠️ Regrouped off a **clean** queryset holding the same trips, not off the
    caller's. `trip_queryset()` already carries an `activities_count`
    annotation, which puts a `GROUP BY trip.id` on the query — grouping again on
    top of that returns one row per trip with a count of 1, silently, for every
    grouping. Re-selecting by id costs one subquery and makes this function
    independent of whatever annotations the caller happens to have added.
    """
    grouped = Trip.objects.filter(pk__in=queryset.values("pk"))

    if group_by == "status":
        counts = dict(grouped.values_list("status").annotate(total=Count("pk", distinct=True)))
        labels = dict(TripStatus.choices)
        return [
            {"key": status, "label": labels[status], "count": counts[status]}
            for status in STATUS_ORDER
            if counts.get(status)
        ]

    if group_by == "month":
        rows = (
            grouped.annotate(month=TruncMonth("start_date"))
            .values("month")
            .annotate(total=Count("pk", distinct=True))
            .order_by("month")
        )
        return [
            {
                "key": row["month"].strftime("%Y-%m"),
                "label": row["month"].strftime("%B %Y"),
                "count": row["total"],
            }
            for row in rows
            if row["month"]
        ]

    if group_by == "country":
        # A trip with stops in two countries counts under both, which is the
        # honest answer for "trips involving France". `distinct=True` stops the
        # join from counting it twice within one country.
        rows = (
            grouped.filter(stops__is_deleted=False)
            .values("stops__city__country", "stops__city__country__name")
            .annotate(total=Count("pk", distinct=True))
            .order_by("-total", "stops__city__country__name")
        )
        return [
            {
                "key": str(row["stops__city__country"]),
                "label": row["stops__city__country__name"],
                "count": row["total"],
            }
            for row in rows
            if row["stops__city__country"]
        ]

    return []


def admin_trip_queryset():
    """
    `GET /admin/trips/` — trip moderation.

    Reads `all_objects` so a moderator can see soft-deleted trips with
    `?include_deleted=true`; the list hides them by default. Otherwise the same
    joins as the user-facing list, so the two report identical numbers.
    """
    return (
        Trip.all_objects.select_related("user")
        .prefetch_related(
            Prefetch(
                "stops",
                queryset=TripStop.objects.select_related("city").order_by("order"),
            )
        )
        .annotate(
            activities_count=Count(
                "stops__activities",
                filter=Q(stops__is_deleted=False, stops__activities__is_deleted=False),
                distinct=True,
            )
        )
        .order_by("-created_at")
    )
