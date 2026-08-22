"""
budget — selectors. Owner: Dev A.

READ layer: querysets, `annotate`, `aggregate`, `select_related` /
`prefetch_related`. Never mutates anything.

The cost *arithmetic* is not here — it is in `services.py`, because the trip
list, the itinerary and the dashboard all import it and there must be exactly
one copy of it.
"""

from apps.budget.models import Expense


def expense_queryset(trip):
    """
    `GET /trips/{id}/expenses/`, scoped to one trip.

    Ownership is already settled by the view's `TripScopedMixin`: the trip was
    resolved against the caller's own trips, so anything hanging off it is
    theirs.
    """
    return Expense.objects.filter(trip=trip).select_related("trip_stop", "trip_stop__city")
