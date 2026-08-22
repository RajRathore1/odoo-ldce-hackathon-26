"""
budget — serializers. Owner: Dev A.

Validation and shaping only. No cross-model writes, no calls into other apps.
"""

from rest_framework import serializers

from apps.budget.models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    """One row of `GET /trips/{id}/expenses/`."""

    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Expense
        fields = (
            "id",
            "category",
            "category_label",
            "title",
            "amount",
            "currency",
            "trip_stop",
            "incurred_on",
            "is_estimated",
            "notes",
            "created_at",
        )


class ExpenseWriteSerializer(serializers.ModelSerializer):
    """
    `POST /trips/{id}/expenses/` and `PATCH .../{id}/`.

    `currency` is absent on purpose: it is inherited from the trip, because the
    budget adds these amounts up without converting.
    """

    class Meta:
        model = Expense
        fields = (
            "category",
            "title",
            "amount",
            "trip_stop",
            "incurred_on",
            "is_estimated",
            "notes",
        )

    def validate_trip_stop(self, stop):
        """A stop from another trip would put spend on somebody else's total."""
        if stop is not None and stop.trip_id != self.context["trip"].pk:
            raise serializers.ValidationError("That stop does not belong to this trip.")
        return stop

    def validate_incurred_on(self, day):
        """
        A day outside the trip would never appear in the budget's `by_day`
        series, so the money would be in the total but on no chart.
        """
        trip = self.context["trip"]
        if day is not None and not trip.start_date <= day <= trip.end_date:
            raise serializers.ValidationError(
                f"This day is outside the trip's dates "
                f"({trip.start_date} to {trip.end_date})."
            )
        return day


# --------------------------------------------------------------- Screen 9


class BudgetBucketSerializer(serializers.Serializer):
    """One slice of the pie. `percentage` is precomputed — do not divide again."""

    category = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    percentage = serializers.FloatField(read_only=True)


class BudgetByStopSerializer(serializers.Serializer):
    stop_id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    budget = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, allow_null=True
    )
    spent = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_over_budget = serializers.BooleanField(read_only=True)


class BudgetByDaySerializer(serializers.Serializer):
    """Every date in the trip range, including the ones with no spend."""

    date = serializers.DateField(read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_over_budget = serializers.BooleanField(read_only=True)


class BudgetAlertSerializer(serializers.Serializer):
    """`date` is null on a trip-wide alert."""

    type = serializers.CharField(read_only=True)
    date = serializers.DateField(read_only=True, allow_null=True)
    message = serializers.CharField(read_only=True)


class TripBudgetSerializer(serializers.Serializer):
    """`GET /trips/{id}/budget/` — the whole of Screen 9 in one response."""

    currency = serializers.CharField(read_only=True)
    total_budget = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, allow_null=True
    )
    grand_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remaining = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, allow_null=True
    )
    is_over_budget = serializers.BooleanField(read_only=True)
    avg_cost_per_day = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    breakdown = BudgetBucketSerializer(many=True, read_only=True)
    by_stop = BudgetByStopSerializer(many=True, read_only=True)
    by_day = BudgetByDaySerializer(many=True, read_only=True)
    alerts = BudgetAlertSerializer(many=True, read_only=True)
