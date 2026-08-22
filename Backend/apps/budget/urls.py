"""
User-facing routes for budget. Mounted by `config/api_urls.py`.

Both prefixes hang off a trip, so they are written out rather than routed: the
trip id is a parent, not a filter.
"""

from django.urls import path

from apps.budget.views import ExpenseDetailView, ExpenseListCreateView, TripBudgetView

urlpatterns = [
    path(
        "trips/<int:trip_id>/expenses/",
        ExpenseListCreateView.as_view(),
        name="trip-expense-list",
    ),
    path(
        "trips/<int:trip_id>/expenses/<int:pk>/",
        ExpenseDetailView.as_view(),
        name="trip-expense-detail",
    ),
    # Screen 9. Not paginated — every part of it is bounded by the trip.
    path(
        "trips/<int:trip_id>/budget/",
        TripBudgetView.as_view(),
        name="trip-budget",
    ),
]
