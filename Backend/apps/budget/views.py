"""
budget — views. Owner: Dev A.

Thin. Parse the request, call a service or selector, return a response.
No business rules and no multi-step ORM work.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.budget import selectors, services
from apps.budget.filters import ExpenseFilterSet
from apps.budget.serializers import (
    ExpenseSerializer,
    ExpenseWriteSerializer,
    TripBudgetSerializer,
)

# `budget → trips` is the legal direction (LAYOUT.md §5), and "resolve `trip_id`
# against the caller's own trips" is a rule that must not exist twice.
from apps.trips.views import TripScopedMixin
from core.response import created, no_content, success


@extend_schema(tags=["expenses"])
class ExpenseListCreateView(TripScopedMixin, generics.ListCreateAPIView):
    """`GET|POST /trips/{trip_id}/expenses/`."""

    filterset_class = ExpenseFilterSet
    search_fields = ("title", "notes")
    ordering_fields = ("incurred_on", "amount", "created_at")
    ordering = ("-incurred_on", "-created_at")

    def get_queryset(self):
        return selectors.expense_queryset(self.trip)

    def get_serializer_class(self):
        return ExpenseWriteSerializer if self.request.method == "POST" else ExpenseSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = services.create_expense(trip=self.trip, **serializer.validated_data)
        return created(data=ExpenseSerializer(expense).data, message="Expense added.")


@extend_schema(tags=["expenses"])
class ExpenseDetailView(TripScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    """`GET|PATCH|DELETE /trips/{trip_id}/expenses/{id}/`."""

    def get_queryset(self):
        return selectors.expense_queryset(self.trip)

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return ExpenseWriteSerializer
        return ExpenseSerializer

    def update(self, request, *args, **kwargs):
        expense = self.get_object()
        serializer = self.get_serializer(
            instance=expense, data=request.data, partial=kwargs.pop("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        expense = services.update_expense(expense, **serializer.validated_data)
        return success(data=ExpenseSerializer(expense).data, message="Expense updated.")

    def destroy(self, request, *args, **kwargs):
        services.delete_expense(self.get_object())
        return no_content()


@extend_schema(
    tags=["budget"], summary="Cost breakdown", responses={200: TripBudgetSerializer}
)
class TripBudgetView(TripScopedMixin, generics.GenericAPIView):
    """
    `GET /trips/{trip_id}/budget/` — Screen 9.

    **Not paginated.** Every part of this response is bounded by the trip: one
    bucket per category, one row per stop, one row per day.
    """

    serializer_class = TripBudgetSerializer
    pagination_class = None

    def get(self, request, *args, **kwargs):
        breakdown = services.trip_budget_breakdown(self.trip)
        return success(data=TripBudgetSerializer(breakdown).data)
