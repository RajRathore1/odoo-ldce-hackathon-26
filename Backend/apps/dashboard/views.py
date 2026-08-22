"""
dashboard — views. Owner: Dev B.

Thin. Parse the request, call a service or selector, return a response.
No business rules and no multi-step ORM work.

Its own app rather than another action on `TripViewSet`, because this endpoint
reads across `trips`, `budget` and `geo` (decision D12) — and because the home
screen is the one place a five-request waterfall would be most visible.
"""

from decimal import Decimal

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.budget.services import bulk_trip_cost_summary
from apps.dashboard import selectors
from apps.dashboard.serializers import DashboardSerializer
from apps.geo.selectors import popular_cities
from apps.trips.constants import TripStatus
from apps.trips.models import Trip
from core.response import success

ZERO = Decimal("0.00")

#: Cards in "Top Regional Selections".
POPULAR_CITIES = 8


@extend_schema(tags=["dashboard"], summary="Home screen", responses={200: DashboardSerializer})
class DashboardView(generics.GenericAPIView):
    """
    `GET /dashboard/` — Screen 3, in one call.

    **Not paginated.** Every part of this response is a bounded top-N: four
    counters, one banner, six trip cards, eight city cards, five money figures.

    Query budget is fixed, not proportional to the user's trip count: the counts
    are one aggregate, the cost figures are three queries for *all* the user's
    trips through `bulk_trip_cost_summary`, and the two card strips are one
    query plus one prefetch each.
    """

    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get(self, request, *args, **kwargs):
        user = request.user

        ongoing = selectors.ongoing_trip(user)
        if ongoing is not None:
            # Attached rather than computed in the serializer: "days left" is a
            # fact about today, not a property of the row.
            ongoing.days_remaining = selectors.days_remaining(ongoing)

        recent = selectors.recent_trips(user)

        # One bulk lookup covering both the cards and the money roll-up, so the
        # two never disagree about the same trip.
        trips = list(
            Trip.objects.filter(user=user).values_list("pk", "status", "total_budget")
        )
        summaries = bulk_trip_cost_summary([pk for pk, _, _ in trips])

        return success(
            data=DashboardSerializer(
                {
                    "user": user,
                    "counts": selectors.trip_counts(user),
                    "ongoing_trip": ongoing,
                    "recent_trips": recent,
                    "popular_cities": popular_cities(limit=POPULAR_CITIES, user=user),
                    "budget_highlights": self._budget_highlights(user, trips, summaries),
                },
                context={"request": request, "cost_summaries": summaries},
            ).data
        )

    @staticmethod
    def _budget_highlights(user, trips, summaries: dict) -> dict:
        """
        Roll the per-trip summaries up. Arithmetic over numbers already fetched
        — no further queries, and no second definition of what a trip costs.
        """
        totals = [summaries.get(pk, {}) for pk, _, _ in trips]
        total_planned = sum((row.get("grand_total") or ZERO for row in totals), ZERO)

        upcoming = sum(
            (
                summaries.get(pk, {}).get("grand_total") or ZERO
                for pk, status, _ in trips
                if status == TripStatus.PLANNED
            ),
            ZERO,
        )

        return {
            "currency": user.currency,
            "total_planned": total_planned,
            "upcoming_trips_budget": upcoming,
            "avg_cost_per_trip": (
                (total_planned / len(trips)).quantize(Decimal("0.01")) if trips else ZERO
            ),
            "over_budget_trips": sum(1 for row in totals if row.get("is_over_budget")),
        }
