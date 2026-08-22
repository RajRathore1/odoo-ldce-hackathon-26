"""dashboard — status codes, envelope shape, permissions."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, UserFactory
from apps.budget.tests.factories import ExpenseFactory
from apps.geo.tests.factories import CityFactory
from apps.trips.constants import TripStatus
from apps.trips.tests.factories import TripActivityFactory, TripFactory, TripStopFactory

pytestmark = pytest.mark.django_db

TODAY = date.today()
URL = reverse("dashboard")


@pytest.fixture
def user():
    return UserFactory(email="riya@example.com", first_name="Riya", currency="INR")


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


def trip_with_content(user, *, start, length, budget=None, status=None, cost="2000.00"):
    """A trip with one stop, one activity and one expense — enough to cost money."""
    trip = TripFactory(
        user=user,
        start_date=start,
        end_date=start + timedelta(days=length - 1),
        total_budget=budget,
        **({"status": status} if status else {}),
    )
    stop = TripStopFactory(trip=trip, start_date=trip.start_date, end_date=trip.end_date)
    TripActivityFactory(trip_stop=stop, day_date=trip.start_date, cost=Decimal(cost))
    ExpenseFactory(trip=trip, amount=Decimal("500.00"), incurred_on=trip.start_date)
    return trip


class TestDashboard:
    def test_it_requires_authentication(self):
        assert APIClient().get(URL).status_code == 401

    def test_it_is_not_paginated(self, client):
        body = client.get(URL).json()["data"]

        assert "pagination" not in body
        assert set(body) == {
            "user",
            "counts",
            "ongoing_trip",
            "recent_trips",
            "popular_cities",
            "budget_highlights",
        }

    def test_an_empty_account_renders_cleanly(self, client):
        """A new user opens this screen before creating anything."""
        body = client.get(URL).json()["data"]

        assert body["counts"] == {
            "total_trips": 0,
            "ongoing": 0,
            "upcoming": 0,
            "completed": 0,
        }
        assert body["ongoing_trip"] is None
        assert body["recent_trips"] == []
        assert body["popular_cities"] == []
        assert body["budget_highlights"]["total_planned"] == "0.00"
        assert body["budget_highlights"]["avg_cost_per_trip"] == "0.00"

    def test_the_user_block_carries_no_pii(self, client, user):
        body = client.get(URL).json()["data"]

        assert body["user"] == {"first_name": "Riya", "avatar": None}

    def test_counts_cover_the_three_tabs(self, client, user):
        trip_with_content(user, start=TODAY - timedelta(days=1), length=4)  # ONGOING
        trip_with_content(user, start=TODAY + timedelta(days=30), length=4)  # PLANNED
        trip_with_content(user, start=TODAY - timedelta(days=40), length=4)  # COMPLETED
        trip_with_content(user, start=TODAY + timedelta(days=60), length=4)  # PLANNED

        counts = client.get(URL).json()["data"]["counts"]

        assert counts == {
            "total_trips": 4,
            "ongoing": 1,
            "upcoming": 2,
            "completed": 1,
        }

    def test_another_users_trips_are_not_counted(self, client, user):
        trip_with_content(UserFactory(), start=TODAY, length=3)

        assert client.get(URL).json()["data"]["counts"]["total_trips"] == 0

    def test_a_deleted_trip_is_not_counted(self, client, user):
        trip_with_content(user, start=TODAY + timedelta(days=5), length=3).delete()

        assert client.get(URL).json()["data"]["counts"]["total_trips"] == 0


class TestOngoingTrip:
    def test_it_is_null_when_the_user_is_not_travelling(self, client, user):
        """B4.3 — the banner has to render without one."""
        trip_with_content(user, start=TODAY + timedelta(days=30), length=4)

        assert client.get(URL).json()["data"]["ongoing_trip"] is None

    def test_it_carries_the_banner_fields(self, client, user):
        trip = trip_with_content(user, start=TODAY - timedelta(days=2), length=6)

        banner = client.get(URL).json()["data"]["ongoing_trip"]

        assert banner["id"] == trip.pk
        assert banner["name"] == trip.name
        assert banner["stops_count"] == 1
        assert banner["days_remaining"] == 3

    def test_a_trip_ending_today_has_no_days_remaining(self, client, user):
        trip_with_content(user, start=TODAY - timedelta(days=3), length=4)

        assert client.get(URL).json()["data"]["ongoing_trip"]["days_remaining"] == 0


class TestRecentTrips:
    def test_newest_first_whatever_the_status(self, client, user):
        older = trip_with_content(user, start=TODAY + timedelta(days=10), length=3)
        newer = trip_with_content(user, start=TODAY - timedelta(days=40), length=3)

        rows = client.get(URL).json()["data"]["recent_trips"]

        assert [row["id"] for row in rows] == [newer.pk, older.pk]

    def test_the_card_carries_a_real_cost(self, client, user):
        trip_with_content(user, start=TODAY + timedelta(days=10), length=3, cost="2000.00")

        card = client.get(URL).json()["data"]["recent_trips"][0]

        # 2000 activity + 500 expense, from the one budget formula.
        assert card["estimated_cost"] == "2500.00"
        assert card["stops_count"] == 1
        assert card["status"] == TripStatus.PLANNED

    def test_the_strip_is_bounded(self, client, user):
        for index in range(9):
            trip_with_content(user, start=TODAY + timedelta(days=10 + index * 5), length=3)

        assert len(client.get(URL).json()["data"]["recent_trips"]) == 6


class TestPopularCities:
    def test_most_popular_first(self, client):
        quiet = CityFactory(name="Quiet", popularity_score=1)
        busy = CityFactory(name="Busy", popularity_score=99)

        rows = client.get(URL).json()["data"]["popular_cities"]

        assert [row["id"] for row in rows] == [busy.pk, quiet.pk]
        assert rows[0]["country_name"] == busy.country.name

    def test_the_strip_is_bounded(self, client):
        CityFactory.create_batch(12)

        assert len(client.get(URL).json()["data"]["popular_cities"]) == 8


class TestBudgetHighlights:
    def test_it_rolls_the_trip_costs_up(self, client, user):
        trip_with_content(user, start=TODAY + timedelta(days=10), length=3, cost="2000.00")
        trip_with_content(user, start=TODAY - timedelta(days=40), length=3, cost="1000.00")

        highlights = client.get(URL).json()["data"]["budget_highlights"]

        assert highlights["currency"] == "INR"
        # (2000 + 500) + (1000 + 500)
        assert highlights["total_planned"] == "4000.00"
        assert highlights["avg_cost_per_trip"] == "2000.00"
        # Only the PLANNED trip counts toward what is still to be spent.
        assert highlights["upcoming_trips_budget"] == "2500.00"

    def test_it_counts_over_budget_trips(self, client, user):
        trip_with_content(
            user,
            start=TODAY + timedelta(days=10),
            length=3,
            budget=Decimal("100.00"),
            cost="2000.00",
        )
        trip_with_content(
            user,
            start=TODAY + timedelta(days=40),
            length=3,
            budget=Decimal("99999.00"),
            cost="2000.00",
        )

        assert client.get(URL).json()["data"]["budget_highlights"]["over_budget_trips"] == 1

    def test_it_agrees_with_the_trip_list(self, client, user):
        """Same formula, so the home screen and Screen 6 cannot disagree."""
        trip_with_content(user, start=TODAY + timedelta(days=10), length=3, cost="1234.00")

        dashboard = client.get(URL).json()["data"]["recent_trips"][0]["estimated_cost"]
        listed = client.get(reverse("trip-list")).json()["data"]["results"][0][
            "estimated_cost"
        ]

        assert dashboard == listed


class TestDashboardQueryBudget:
    def test_the_query_count_does_not_grow_with_the_account(
        self, client, user, django_assert_num_queries
    ):
        """
        B4.4. The whole point of this endpoint is that it is one bounded call —
        if it scaled with the trip count it would be worse than the waterfall it
        replaces.
        """
        for index in range(2):
            trip_with_content(user, start=TODAY + timedelta(days=10 + index * 5), length=3)
        CityFactory.create_batch(3)

        # Ten, and always ten: the authenticating user, the ongoing trip and its
        # stops, the recent trips and their stops, one pass over the trip ids,
        # three for `bulk_trip_cost_summary`, and the popular cities.
        with django_assert_num_queries(10) as captured:
            client.get(URL)

        for index in range(8):
            trip_with_content(user, start=TODAY + timedelta(days=90 + index * 5), length=3)
        CityFactory.create_batch(10)

        with django_assert_num_queries(len(captured.captured_queries)):
            client.get(URL)
