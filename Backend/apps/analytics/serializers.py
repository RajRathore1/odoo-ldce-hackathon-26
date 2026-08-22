"""
analytics — serializers. Owner: Dev B.

Validation and shaping only. No cross-model writes, no calls into other apps.

Read-only by definition: analytics has no writes to validate.
"""

from rest_framework import serializers


class UserTileSerializer(serializers.Serializer):
    total = serializers.IntegerField(read_only=True)
    active = serializers.IntegerField(read_only=True)
    new_this_period = serializers.IntegerField(read_only=True)
    growth_pct = serializers.FloatField(read_only=True)


class TripTileSerializer(serializers.Serializer):
    total = serializers.IntegerField(read_only=True)
    created_this_period = serializers.IntegerField(read_only=True)
    public = serializers.IntegerField(read_only=True)
    avg_stops_per_trip = serializers.FloatField(read_only=True)


class BudgetTileSerializer(serializers.Serializer):
    avg_trip_budget = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    currency = serializers.CharField(read_only=True)
    total_planned_value = serializers.DecimalField(
        max_digits=16, decimal_places=2, read_only=True
    )


class ContentTileSerializer(serializers.Serializer):
    """Zeros while the community app is cut — the tile still renders."""

    posts = serializers.IntegerField(read_only=True)
    comments = serializers.IntegerField(read_only=True)


class AnalyticsOverviewSerializer(serializers.Serializer):
    """`GET /admin/analytics/overview/` — the KPI tiles on Screen 13."""

    users = UserTileSerializer(read_only=True)
    trips = TripTileSerializer(read_only=True)
    budget = BudgetTileSerializer(read_only=True)
    content = ContentTileSerializer(read_only=True)
    period = serializers.CharField(read_only=True)
