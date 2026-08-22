"""
dashboard — serializers. Owner: Dev B.

Validation and shaping only. No cross-model writes, no calls into other apps.

Every shape here is **smaller** than the equivalent on the resource's own
endpoint. A home screen renders cards, so it wants six fields per trip and five
per city, not the forty the detail endpoints return — sending the full shapes
would make the one call that exists to avoid a waterfall heavier than the
waterfall.
"""

from rest_framework import serializers

from apps.accounts.serializers import PublicUserSerializer
from apps.geo.models import City
from apps.trips.models import Trip


class DashboardCountsSerializer(serializers.Serializer):
    """The header counters. Screen 6's tabs are built from the same three."""

    total_trips = serializers.IntegerField(read_only=True)
    ongoing = serializers.IntegerField(read_only=True)
    upcoming = serializers.IntegerField(read_only=True)
    completed = serializers.IntegerField(read_only=True)


class OngoingTripSerializer(serializers.ModelSerializer):
    """The "you are travelling" banner. `null` when the user is not."""

    stops_count = serializers.SerializerMethodField()
    days_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = Trip
        fields = (
            "id",
            "name",
            "start_date",
            "end_date",
            "stops_count",
            "days_remaining",
            "cover_photo",
        )

    def get_stops_count(self, trip) -> int:
        """Off the prefetch — this is one object, but the habit matters."""
        return len(trip.stops.all())


class DashboardTripSerializer(serializers.ModelSerializer):
    """One card in the "Previous Trips" strip."""

    stops_count = serializers.SerializerMethodField()
    estimated_cost = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = (
            "id",
            "name",
            "status",
            "start_date",
            "end_date",
            "stops_count",
            "estimated_cost",
            "currency",
            "cover_photo",
        )

    def get_stops_count(self, trip) -> int:
        return len(trip.stops.all())

    def get_estimated_cost(self, trip) -> str:
        """From the page-wide bulk cost lookup in `context`, never per row."""
        summary = self.context.get("cost_summaries", {}).get(trip.pk)
        return str(summary["grand_total"]) if summary else "0.00"


class DashboardCitySerializer(serializers.ModelSerializer):
    """One card in "Top Regional Selections"."""

    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = City
        fields = ("id", "name", "country_name", "popularity_score", "image_url")


class BudgetHighlightsSerializer(serializers.Serializer):
    """
    Money, rolled up across the user's trips.

    Every figure is derived from `budget.services.bulk_trip_cost_summary`, so
    these agree with the trip list and Screen 9 by construction.
    """

    currency = serializers.CharField(read_only=True)
    total_planned = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    upcoming_trips_budget = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    avg_cost_per_trip = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    over_budget_trips = serializers.IntegerField(read_only=True)


class DashboardSerializer(serializers.Serializer):
    """`GET /dashboard/` — the whole of Screen 3 in one response."""

    user = PublicUserSerializer(read_only=True)
    counts = DashboardCountsSerializer(read_only=True)
    ongoing_trip = OngoingTripSerializer(read_only=True, allow_null=True)
    recent_trips = DashboardTripSerializer(many=True, read_only=True)
    popular_cities = DashboardCitySerializer(many=True, read_only=True)
    budget_highlights = BudgetHighlightsSerializer(read_only=True)
