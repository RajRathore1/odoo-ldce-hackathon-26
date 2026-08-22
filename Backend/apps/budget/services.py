"""
budget — services. Owner: Dev A.

WRITE layer + **the single cost formula**.

`trip_cost_summary(trip)` and `bulk_trip_cost_summary(trip_ids)` live here
and nowhere else. The trip list, trip detail, itinerary totals and the
dashboard all import them. Re-deriving the arithmetic anywhere else is how
the four screens start disagreeing about the same trip.
"""

import logging
from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.budget.constants import (
    DAY_ALERT_TOLERANCE,
    AlertType,
    ExpenseCategory,
)
from apps.budget.models import Expense
from apps.trips.models import Trip, TripActivity, TripStop
from core.utils import daterange, days_inclusive

logger = logging.getLogger(__name__)

ZERO = Decimal("0.00")


def _quantise(value: Decimal) -> Decimal:
    """Two decimal places, so every amount serialises as `"1234.50"`."""
    return (value or ZERO).quantize(Decimal("0.01"))


def _summarise(
    *,
    activities_cost: Decimal,
    expenses_cost: Decimal,
    total_budget: Decimal | None,
    duration_days: int,
) -> dict:
    """
    **The formula.** Everything else in this module feeds it numbers.

    `remaining` is `None` rather than `0` when no budget was set: "you have
    nothing left" and "you never said" are different answers, and Screen 9 shows
    them differently.
    """
    activities_cost = _quantise(activities_cost)
    expenses_cost = _quantise(expenses_cost)
    grand_total = activities_cost + expenses_cost

    return {
        "activities_cost": activities_cost,
        "expenses_cost": expenses_cost,
        "grand_total": grand_total,
        "avg_per_day": _quantise(grand_total / duration_days) if duration_days else ZERO,
        "remaining": _quantise(total_budget - grand_total) if total_budget else None,
        "is_over_budget": total_budget is not None and grand_total > total_budget,
    }


def trip_cost_summary(trip: Trip) -> dict:
    """
    What one trip costs. Two aggregate queries.

    The `trip_stop__is_deleted=False` filter is load-bearing: soft delete does
    not cascade, so a removed stop's activities are still live rows and would
    keep counting (trap #2).
    """
    activities_cost = TripActivity.objects.filter(
        trip_stop__trip=trip, trip_stop__is_deleted=False
    ).aggregate(total=Sum("cost"))["total"]
    expenses_cost = Expense.objects.filter(trip=trip).aggregate(total=Sum("amount"))["total"]

    return _summarise(
        activities_cost=activities_cost or ZERO,
        expenses_cost=expenses_cost or ZERO,
        total_budget=trip.total_budget,
        duration_days=trip.duration_days,
    )


def bulk_trip_cost_summary(trip_ids) -> dict[int, dict]:
    """
    The same payload for many trips, keyed by trip id, in **three** queries.

    Use this one in every list endpoint and on `/dashboard/`. Calling
    `trip_cost_summary` per row is what turns a 20-trip page into 40 queries
    (trap #9).
    """
    trip_ids = list(trip_ids)
    if not trip_ids:
        return {}

    activities = dict(
        TripActivity.objects.filter(
            trip_stop__trip_id__in=trip_ids, trip_stop__is_deleted=False
        )
        .values_list("trip_stop__trip_id")
        .annotate(total=Sum("cost"))
    )
    expenses = dict(
        Expense.objects.filter(trip_id__in=trip_ids)
        .values_list("trip_id")
        .annotate(total=Sum("amount"))
    )
    trips = Trip.objects.filter(pk__in=trip_ids).values_list(
        "pk", "total_budget", "start_date", "end_date"
    )

    return {
        pk: _summarise(
            activities_cost=activities.get(pk) or ZERO,
            expenses_cost=expenses.get(pk) or ZERO,
            total_budget=total_budget,
            duration_days=days_inclusive(start_date, end_date),
        )
        for pk, total_budget, start_date, end_date in trips
    }


def platform_cost_totals() -> dict:
    """
    The same formula, aggregated across **every** trip. Two queries.

    Mathematically the sum of every `trip_cost_summary`'s `grand_total`, which is
    why it lives here next to them rather than in `analytics`: it is cost
    arithmetic, and there is one module for that. Looping
    `bulk_trip_cost_summary` over every trip on the platform would give the same
    answer and scan the whole table to do it.

    Note the absence of currency handling — a platform-wide total mixes them, so
    the caller has to say what it is presenting. See `analytics.selectors`.
    """
    activities_cost = TripActivity.objects.filter(
        trip_stop__is_deleted=False, trip_stop__trip__is_deleted=False
    ).aggregate(total=Sum("cost"))["total"]
    expenses_cost = Expense.objects.filter(trip__is_deleted=False).aggregate(
        total=Sum("amount")
    )["total"]

    activities_cost = _quantise(activities_cost or ZERO)
    expenses_cost = _quantise(expenses_cost or ZERO)
    return {
        "activities_cost": activities_cost,
        "expenses_cost": expenses_cost,
        "grand_total": activities_cost + expenses_cost,
    }

def trip_budget_breakdown(trip: Trip) -> dict:
    """
    The whole Screen 9 payload: buckets, per-stop, per-day and alerts.

    Labels and percentages are precomputed — the frontend should not be dividing
    to draw a pie. Only non-zero buckets are returned, so the chart has no empty
    slices to filter out.

    ⚠️ **`ACTIVITY` is the one bucket with two sources** (trap #5): the
    snapshotted `TripActivity.cost` values *plus* `Expense` rows filed under
    `ACTIVITY`. Adding them here, once, is what stops the pie and the trip total
    from disagreeing.
    """
    summary = trip_cost_summary(trip)

    activity_rows = list(
        TripActivity.objects.filter(
            trip_stop__trip=trip, trip_stop__is_deleted=False
        ).values_list("trip_stop_id", "day_date", "cost")
    )
    expense_rows = list(
        Expense.objects.filter(trip=trip).values_list(
            "trip_stop_id", "incurred_on", "category", "amount"
        )
    )

    # --- buckets
    buckets: dict[str, Decimal] = defaultdict(lambda: ZERO)
    buckets[ExpenseCategory.ACTIVITY] += sum((row[2] for row in activity_rows), ZERO)
    for _, _, category, amount in expense_rows:
        buckets[category] += amount

    labels = dict(ExpenseCategory.choices)
    grand_total = summary["grand_total"]
    breakdown = [
        {
            "category": category,
            "label": labels[category],
            "amount": _quantise(amount),
            "percentage": (
                float(round(amount / grand_total * 100, 1)) if grand_total else 0.0
            ),
        }
        for category, amount in buckets.items()
        if amount
    ]
    breakdown.sort(key=lambda bucket: bucket["amount"], reverse=True)

    # --- per stop
    spent_by_stop: dict[int, Decimal] = defaultdict(lambda: ZERO)
    for stop_id, _, cost in activity_rows:
        spent_by_stop[stop_id] += cost
    for stop_id, _, _, amount in expense_rows:
        if stop_id is not None:
            spent_by_stop[stop_id] += amount

    by_stop = []
    for stop in TripStop.objects.filter(trip=trip).order_by("order"):
        spent = _quantise(spent_by_stop.get(stop.pk, ZERO))
        by_stop.append(
            {
                "stop_id": stop.pk,
                "title": stop.display_title,
                "budget": stop.budget,
                "spent": spent,
                "is_over_budget": stop.budget is not None and spent > stop.budget,
            }
        )

    # --- per day
    spent_by_day: dict = defaultdict(lambda: ZERO)
    for _, day_date, cost in activity_rows:
        spent_by_day[day_date] += cost
    for _, incurred_on, _, amount in expense_rows:
        if incurred_on is not None:
            spent_by_day[incurred_on] += amount

    duration_days = trip.duration_days
    daily_allowance = (
        _quantise(trip.total_budget / duration_days)
        if trip.total_budget and duration_days
        else None
    )

    by_day, alerts = [], []
    for day in daterange(trip.start_date, trip.end_date):
        amount = _quantise(spent_by_day.get(day, ZERO))
        over = daily_allowance is not None and amount > daily_allowance
        by_day.append({"date": day, "amount": amount, "is_over_budget": over})

        if over and amount > daily_allowance * (1 + Decimal(str(DAY_ALERT_TOLERANCE))):
            percent = int(round((amount / daily_allowance - 1) * 100))
            alerts.append(
                {
                    "type": AlertType.OVERBUDGET_DAY,
                    "date": day,
                    "message": (f"{day} exceeds the average daily budget by {percent}%."),
                }
            )

    if summary["is_over_budget"]:
        alerts.insert(
            0,
            {
                "type": AlertType.OVERBUDGET_TRIP,
                "date": None,
                "message": (
                    f"This trip is {_quantise(grand_total - trip.total_budget)} "
                    f"{trip.currency} over its {trip.total_budget} budget."
                ),
            },
        )

    return {
        "currency": trip.currency,
        "total_budget": trip.total_budget,
        "grand_total": grand_total,
        "remaining": summary["remaining"],
        "is_over_budget": summary["is_over_budget"],
        "avg_cost_per_day": summary["avg_per_day"],
        "breakdown": breakdown,
        "by_stop": by_stop,
        "by_day": by_day,
        "alerts": alerts,
    }


# ------------------------------------------------------------------- expenses


@transaction.atomic
def create_expense(*, trip: Trip, **fields) -> Expense:
    """
    Record spend against a trip.

    `currency` comes from the trip, like every other amount hanging off it — see
    `trips.services.create_trip_activity` for why that is not negotiable.
    """
    fields["currency"] = trip.currency
    expense = Expense.objects.create(trip=trip, **fields)
    logger.info("Expense %s (%s) added to trip %s", expense.pk, expense.category, trip.pk)
    return expense


@transaction.atomic
def update_expense(expense: Expense, **fields) -> Expense:
    for name, value in fields.items():
        setattr(expense, name, value)
    expense.save()
    return expense


def delete_expense(expense: Expense) -> None:
    expense.delete()
    logger.info("Expense %s soft-deleted", expense.pk)
