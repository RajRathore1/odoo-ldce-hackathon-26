"""budget — status codes, envelope shape, permissions."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, UserFactory
from apps.budget.constants import ExpenseCategory
from apps.budget.models import Expense
from apps.budget.tests.factories import ExpenseFactory
from apps.trips.tests.factories import TripActivityFactory, TripFactory, TripStopFactory

pytestmark = pytest.mark.django_db

TODAY = date.today()


@pytest.fixture
def user():
    return UserFactory(email="riya@example.com")


@pytest.fixture
def other_user():
    return UserFactory(email="someone-else@example.com")


@pytest.fixture
def client(user):
    api = APIClient()
    response = api.post(
        reverse("auth-login"),
        {"email": user.email, "password": DEFAULT_PASSWORD},
        format="json",
    )
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['tokens']['access']}")
    return api


@pytest.fixture
def trip(user):
    return TripFactory(
        user=user,
        start_date=TODAY + timedelta(days=30),
        end_date=TODAY + timedelta(days=39),
        total_budget=Decimal("50000.00"),
    )


@pytest.fixture
def stop(trip):
    return TripStopFactory(
        trip=trip,
        order=1,
        start_date=trip.start_date,
        end_date=trip.start_date + timedelta(days=4),
        budget=Decimal("18000.00"),
    )


def expenses_url(trip_id) -> str:
    return reverse("trip-expense-list", args=[trip_id])


def expense_detail_url(trip_id, expense_id) -> str:
    return reverse("trip-expense-detail", args=[trip_id, expense_id])


def budget_url(trip_id) -> str:
    return reverse("trip-budget", args=[trip_id])


class TestExpenseCreate:
    def payload(self, trip, **overrides) -> dict:
        data = {
            "category": ExpenseCategory.STAY,
            "title": "Guesthouse, three nights",
            "amount": "14000.00",
            "incurred_on": str(trip.start_date),
        }
        return {**data, **overrides}

    def test_it_records_an_expense(self, client, trip):
        response = client.post(expenses_url(trip.pk), self.payload(trip), format="json")
        body = response.json()

        assert response.status_code == 201
        assert body["message"] == "Expense added."
        assert body["data"]["amount"] == "14000.00"
        assert body["data"]["category"] == ExpenseCategory.STAY
        assert body["data"]["category_label"] == "Stay"
        assert body["data"]["is_estimated"] is True

    def test_currency_is_inherited_from_the_trip(self, client, trip):
        trip.currency = "EUR"
        trip.save(update_fields=["currency"])

        response = client.post(
            expenses_url(trip.pk), self.payload(trip, currency="USD"), format="json"
        )

        assert response.json()["data"]["currency"] == "EUR"

    def test_it_can_be_attached_to_a_stop(self, client, trip, stop):
        response = client.post(
            expenses_url(trip.pk), self.payload(trip, trip_stop=stop.pk), format="json"
        )

        assert response.status_code == 201
        assert response.json()["data"]["trip_stop"] == stop.pk

    def test_a_stop_from_another_trip_is_rejected(self, client, trip):
        stranger = TripStopFactory()

        response = client.post(
            expenses_url(trip.pk), self.payload(trip, trip_stop=stranger.pk), format="json"
        )

        assert response.status_code == 400
        assert "trip_stop" in response.json()["errors"]["fields"]

    def test_a_day_outside_the_trip_is_rejected(self, client, trip):
        response = client.post(
            expenses_url(trip.pk),
            self.payload(trip, incurred_on=str(trip.end_date + timedelta(days=1))),
            format="json",
        )

        assert response.status_code == 400
        assert "incurred_on" in response.json()["errors"]["fields"]

    def test_no_day_at_all_is_fine(self, client, trip):
        """ "The flights" do not belong to a particular day of the trip."""
        response = client.post(
            expenses_url(trip.pk),
            self.payload(trip, incurred_on=None, category=ExpenseCategory.TRANSPORT),
            format="json",
        )

        assert response.status_code == 201
        assert response.json()["data"]["incurred_on"] is None

    def test_an_unknown_category_is_rejected(self, client, trip):
        response = client.post(
            expenses_url(trip.pk), self.payload(trip, category="FLIGHTS"), format="json"
        )

        assert response.status_code == 400

    def test_cannot_add_an_expense_to_somebody_elses_trip(self, client, other_user):
        stranger = TripFactory(user=other_user)

        response = client.post(
            expenses_url(stranger.pk), self.payload(stranger), format="json"
        )

        assert response.status_code == 404
        assert not Expense.objects.exists()


class TestExpenseList:
    def test_it_lists_only_this_trips_expenses(self, client, trip):
        mine = ExpenseFactory(trip=trip)
        ExpenseFactory()  # another trip entirely

        body = client.get(expenses_url(trip.pk)).json()

        assert [row["id"] for row in body["data"]["results"]] == [mine.pk]

    def test_it_filters_by_category(self, client, trip):
        stay = ExpenseFactory(trip=trip, category=ExpenseCategory.STAY)
        ExpenseFactory(trip=trip, category=ExpenseCategory.MEALS)

        body = client.get(expenses_url(trip.pk), {"category": "STAY"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [stay.pk]

    def test_it_filters_by_stop(self, client, trip, stop):
        on_stop = ExpenseFactory(trip=trip, trip_stop=stop)
        ExpenseFactory(trip=trip, trip_stop=None)

        body = client.get(expenses_url(trip.pk), {"trip_stop": stop.pk}).json()

        assert [row["id"] for row in body["data"]["results"]] == [on_stop.pk]

    def test_a_deleted_expense_is_hidden(self, client, trip):
        ExpenseFactory(trip=trip).delete()

        assert client.get(expenses_url(trip.pk)).json()["data"]["pagination"]["count"] == 0


class TestExpenseDetail:
    def test_patch_updates_it(self, client, trip):
        expense = ExpenseFactory(trip=trip)

        response = client.patch(
            expense_detail_url(trip.pk, expense.pk),
            {"amount": "1234.50", "is_estimated": False},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Expense updated."
        expense.refresh_from_db()
        assert expense.amount == Decimal("1234.50")
        assert expense.is_estimated is False

    def test_delete_soft_deletes_it(self, client, trip):
        expense = ExpenseFactory(trip=trip)

        response = client.delete(expense_detail_url(trip.pk, expense.pk))

        assert response.status_code == 204
        assert not Expense.objects.filter(pk=expense.pk).exists()
        assert Expense.all_objects.filter(pk=expense.pk).exists()

    def test_somebody_elses_expense_is_a_404(self, client, other_user):
        stranger_trip = TripFactory(user=other_user)
        stranger_expense = ExpenseFactory(trip=stranger_trip)

        response = client.get(expense_detail_url(stranger_trip.pk, stranger_expense.pk))

        assert response.status_code == 404


class TestTripBudget:
    def test_it_is_not_paginated(self, client, trip):
        body = client.get(budget_url(trip.pk)).json()

        assert "pagination" not in body["data"]
        assert body["data"]["currency"] == "INR"

    def test_the_whole_screen_9_payload(self, client, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("2500.00"))
        ExpenseFactory(
            trip=trip,
            trip_stop=stop,
            category=ExpenseCategory.STAY,
            amount=Decimal("7500.00"),
            incurred_on=stop.start_date,
        )

        body = client.get(budget_url(trip.pk)).json()["data"]

        assert body["total_budget"] == "50000.00"
        assert body["grand_total"] == "10000.00"
        assert body["remaining"] == "40000.00"
        assert body["is_over_budget"] is False
        assert body["avg_cost_per_day"] == "1000.00"

        assert body["breakdown"] == [
            {
                "category": "STAY",
                "label": "Stay",
                "amount": "7500.00",
                "percentage": 75.0,
            },
            {
                "category": "ACTIVITY",
                "label": "Activities",
                "amount": "2500.00",
                "percentage": 25.0,
            },
        ]
        assert body["by_stop"] == [
            {
                "stop_id": stop.pk,
                "title": stop.display_title,
                "budget": "18000.00",
                "spent": "10000.00",
                "is_over_budget": False,
            }
        ]
        assert len(body["by_day"]) == 10
        assert body["by_day"][0]["amount"] == "10000.00"
        assert body["by_day"][0]["is_over_budget"] is True
        assert body["alerts"][0]["type"] == "OVERBUDGET_DAY"

    def test_a_trip_with_nothing_on_it_still_answers(self, client, trip):
        body = client.get(budget_url(trip.pk)).json()["data"]

        assert body["grand_total"] == "0.00"
        assert body["breakdown"] == []
        assert body["by_stop"] == []
        assert body["alerts"] == []
        assert len(body["by_day"]) == 10

    def test_somebody_elses_budget_is_a_404(self, client, other_user):
        assert client.get(budget_url(TripFactory(user=other_user).pk)).status_code == 404

    def test_it_requires_authentication(self, trip):
        assert APIClient().get(budget_url(trip.pk)).status_code == 401


class TestCostsReachTheOtherScreens:
    """A6.3 and A6.8 — the numbers the trip list and the itinerary read."""

    def test_the_trip_list_row_carries_the_real_cost(self, client, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("2500.00"))
        ExpenseFactory(trip=trip, amount=Decimal("1500.00"))

        row = client.get(reverse("trip-list")).json()["data"]["results"][0]

        assert row["estimated_cost"] == "4000.00"
        assert row["is_over_budget"] is False

    def test_the_trip_list_flags_an_over_budget_trip(self, client, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("60000.00"))

        row = client.get(reverse("trip-list")).json()["data"]["results"][0]

        assert row["estimated_cost"] == "60000.00"
        assert row["is_over_budget"] is True

    def test_the_itinerary_totals_are_filled_in(self, client, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("2500.00"))
        ExpenseFactory(trip=trip, amount=Decimal("1500.00"))

        body = client.get(reverse("trip-itinerary", args=[trip.pk])).json()["data"]

        assert body["totals"] == {
            "activities_cost": "2500.00",
            "expenses_cost": "1500.00",
            "grand_total": "4000.00",
        }

    def test_the_itinerary_day_total_counts_activities_only(self, client, trip, stop):
        """
        The itinerary's `day_total_cost` is the day's activities. The budget's
        `by_day` adds that day's expenses on top — two different questions.
        """
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("2500.00"))
        ExpenseFactory(trip=trip, amount=Decimal("1500.00"), incurred_on=stop.start_date)

        itinerary = client.get(reverse("trip-itinerary", args=[trip.pk])).json()["data"]
        budget = client.get(budget_url(trip.pk)).json()["data"]

        assert itinerary["days"][0]["day_total_cost"] == "2500.00"
        assert budget["by_day"][0]["amount"] == "4000.00"
