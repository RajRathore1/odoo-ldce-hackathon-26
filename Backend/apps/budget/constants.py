"""
budget — constants. Owner: Dev A.

`TextChoices` classes, enums and magic numbers. Import these into
`models.py` rather than declaring choices inline.
"""

from django.db import models


class ExpenseCategory(models.TextChoices):
    """
    The buckets of the Screen 9 pie chart.

    ⚠️ `ACTIVITY` is the one bucket with **two** sources: the snapshotted
    `TripActivity.cost` values *plus* any `Expense` row filed under it. See
    `services.trip_cost_summary` — that is the only place the sum is written.
    """

    TRANSPORT = "TRANSPORT", "Transport"
    STAY = "STAY", "Stay"
    ACTIVITY = "ACTIVITY", "Activities"
    MEALS = "MEALS", "Meals"
    SHOPPING = "SHOPPING", "Shopping"
    OTHER = "OTHER", "Other"


class AlertType(models.TextChoices):
    """What `GET /trips/{id}/budget/` warns about. Both need a `total_budget`."""

    OVERBUDGET_TRIP = "OVERBUDGET_TRIP", "Trip is over budget"
    OVERBUDGET_DAY = "OVERBUDGET_DAY", "Day is over the average daily budget"


#: A day has to exceed the average daily budget by this fraction before it earns
#: an alert. Without a threshold every uneven day generates noise — a trip with
#: one museum ticket would raise five alerts on a five-day plan.
DAY_ALERT_TOLERANCE = 0.10
