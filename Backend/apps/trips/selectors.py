"""
trips — selectors. Owner: Dev A.

READ layer: querysets, `annotate`, `aggregate`, `select_related` /
`prefetch_related`. Never mutates anything.
"""

from decimal import Decimal

from apps.trips.models import Trip

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
    Trap #9: this must stay a bounded number of queries whatever the page size.
    """
    return Trip.objects.select_related("user")


def cost_summaries_for(trip_ids) -> dict[int, dict]:
    """
    `{trip_id: cost summary}` for a whole page, in one query.

    ⚠️ **Returns zeros until task A6.** `estimated_cost` and `is_over_budget`
    come from `budget.services.bulk_trip_cost_summary`, which needs the
    `Expense` and `TripActivity` tables. This is the single call site, so
    landing A6 is a change to this function's body and nothing else — the
    serializer already renders whatever it returns.
    """
    return dict.fromkeys(trip_ids, ZERO_COST_SUMMARY)
