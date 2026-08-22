"""
budget — models. Owner: Dev A.

`Expense` — see docs/MODELS.md §7.

One model, because activity costs already live on `trips.TripActivity`. An
`Expense` is everything a trip costs that is *not* an activity — the flight, the
hotel, the meals — plus the occasional activity-shaped one-off the catalog does
not have a row for (decision D4).
"""

from django.db import models

from apps.budget.constants import ExpenseCategory
from core.models import BaseModel


class Expense(BaseModel):
    """
    One line of spend on a trip.

    `trip_stop` is optional: a flight belongs to the trip, a dinner belongs to
    the city you were in. When it is set, the expense also shows up in the
    budget's `by_stop` breakdown.
    """

    trip = models.ForeignKey("trips.Trip", on_delete=models.CASCADE, related_name="expenses")
    trip_stop = models.ForeignKey(
        "trips.TripStop",
        # SET_NULL: removing a section must not delete the money spent in it, or
        # the trip total would silently drop.
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
    )

    category = models.CharField(max_length=10, choices=ExpenseCategory.choices, db_index=True)
    title = models.CharField(max_length=150)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    # Inherited from the trip, never taken from the client — the budget adds
    # these up without converting.
    currency = models.CharField(max_length=3, default="INR")

    # Which day the money lands on, for the budget's `by_day` series. Optional:
    # "the flights" do not belong to a particular day of the trip.
    incurred_on = models.DateField(null=True, blank=True)
    # Estimates are what a *plan* is made of; the flag lets the frontend show
    # planned versus actual without a second table.
    is_estimated = models.BooleanField(default=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-incurred_on", "-created_at")
        indexes = [
            models.Index(fields=["trip", "category"], name="expense_trip_category_idx"),
            models.Index(fields=["trip", "incurred_on"], name="expense_trip_day_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.amount} {self.currency})"
