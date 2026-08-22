"""
dashboard — selectors. Owner: Dev B.

READ layer: querysets, `annotate`, `aggregate`, `select_related` /
`prefetch_related`. Never mutates anything.

Nothing here computes money. The cost numbers come from
`budget.services.bulk_trip_cost_summary`, which is the one place the formula
lives — a dashboard that adds costs up its own way is a dashboard that disagrees
with the trip list (`CLAUDE.md` trap #5).
"""

from django.db.models import Count, Q
from django.utils import timezone

from apps.trips.constants import TripStatus
from apps.trips.models import Trip

#: How many trips the "Previous Trips" strip carries. Bounded on purpose — this
#: is a home screen, not the trip list.
RECENT_TRIPS = 6


def trip_counts(user) -> dict:
    """
    The four header counters, in **one** query.

    Five separate `count()` calls would be the obvious implementation and four
    queries too many on the screen every user opens first.
    """
    return Trip.objects.filter(user=user).aggregate(
        total_trips=Count("pk"),
        ongoing=Count("pk", filter=Q(status=TripStatus.ONGOING)),
        upcoming=Count("pk", filter=Q(status=TripStatus.PLANNED)),
        completed=Count("pk", filter=Q(status=TripStatus.COMPLETED)),
    )


def ongoing_trip(user):
    """
    The trip the user is on right now, or `None`.

    `None` is the normal case, not an error state — most users are not travelling
    today, and the banner has to render cleanly without one (task B4.3).
    """
    return (
        Trip.objects.filter(user=user, status=TripStatus.ONGOING)
        .prefetch_related("stops")
        .order_by("start_date")
        .first()
    )


def recent_trips(user, limit: int = RECENT_TRIPS):
    """The "Previous Trips" strip — newest first, whatever their status."""
    return list(
        Trip.objects.filter(user=user)
        .prefetch_related("stops")
        .order_by("-created_at")[:limit]
    )


def days_remaining(trip) -> int:
    """
    Whole days left, not counting today.

    A trip ending today has 0 days remaining, which is what "last day" means on
    the banner.
    """
    if trip is None or trip.end_date is None:
        return 0
    return max((trip.end_date - timezone.localdate()).days, 0)
