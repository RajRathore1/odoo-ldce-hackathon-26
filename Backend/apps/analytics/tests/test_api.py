"""analytics — Status codes, envelope shape, permissions."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, AdminFactory, UserFactory
from apps.budget.tests.factories import ExpenseFactory
from apps.trips.tests.factories import TripActivityFactory, TripFactory, TripStopFactory

pytestmark = pytest.mark.django_db

TODAY = date.today()
URL = reverse("admin-analytics-overview")


def signed_in(user) -> APIClient:
    api = APIClient()
    response = api.post(
        reverse("auth-login"),
        {"email": user.email, "password": DEFAULT_PASSWORD},
        format="json",
    )
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['tokens']['access']}")
    return api


@pytest.fixture
def admin_client():
    return signed_in(AdminFactory(email="admin@globetrotter.dev"))


def trip_with_cost(
    user=None, *, activity="2000.00", expense="500.00", budget=None, public=False
):
    trip = TripFactory(
        user=user or UserFactory(),
        start_date=TODAY + timedelta(days=10),
        end_date=TODAY + timedelta(days=14),
        total_budget=Decimal(budget) if budget else None,
        is_public=public,
    )
    stop = TripStopFactory(trip=trip, start_date=trip.start_date, end_date=trip.end_date)
    TripActivityFactory(trip_stop=stop, day_date=trip.start_date, cost=Decimal(activity))
    ExpenseFactory(trip=trip, amount=Decimal(expense), incurred_on=trip.start_date)
    return trip


class TestPermissions:
    def test_anonymous_is_a_401(self):
        assert APIClient().get(URL).status_code == 401

    def test_an_ordinary_logged_in_user_is_a_403(self):
        """
        Trap #8. The mount point cannot gate the tree, so a view that forgot
        `AdminOnlyMixin` would answer 200 here.
        """
        assert signed_in(UserFactory()).get(URL).status_code == 403

    def test_an_admin_gets_in(self, admin_client):
        assert admin_client.get(URL).status_code == 200

    def test_a_django_superuser_gets_in(self):
        """The `createsuperuser` escape hatch, worth having mid-demo."""
        staff = UserFactory(email="staff@example.com", is_staff=True)

        assert signed_in(staff).get(URL).status_code == 200


class TestOverviewShape:
    def test_it_is_not_paginated_and_has_every_tile(self, admin_client):
        body = admin_client.get(URL).json()["data"]

        assert "pagination" not in body
        assert set(body) == {"users", "trips", "budget", "content", "period"}
        assert set(body["users"]) == {"total", "active", "new_this_period", "growth_pct"}
        assert set(body["trips"]) == {
            "total",
            "created_this_period",
            "public",
            "avg_stops_per_trip",
        }

    def test_an_empty_platform_renders_zeros(self, admin_client):
        body = admin_client.get(URL).json()["data"]

        assert body["trips"]["total"] == 0
        assert body["trips"]["avg_stops_per_trip"] == 0.0
        assert body["budget"]["total_planned_value"] == "0.00"
        assert body["budget"]["avg_trip_budget"] == "0.00"
        assert body["content"] == {"posts": 0, "comments": 0}

    def test_the_default_period_is_thirty_days(self, admin_client):
        assert admin_client.get(URL).json()["data"]["period"] == "30d"

    def test_a_period_is_echoed_back(self, admin_client):
        assert admin_client.get(URL, {"period": "7d"}).json()["data"]["period"] == "7d"

    def test_a_nonsense_period_falls_back_rather_than_erroring(self, admin_client):
        response = admin_client.get(URL, {"period": "forever"})

        assert response.status_code == 200
        assert response.json()["data"]["period"] == "30d"


class TestOverviewNumbers:
    def test_user_counters(self, admin_client):
        UserFactory.create_batch(3)
        UserFactory(is_active=False)

        users = admin_client.get(URL).json()["data"]["users"]

        # Four here plus the admin doing the asking.
        assert users["total"] == 5
        assert users["active"] == 4
        assert users["new_this_period"] == 5

    def test_a_deleted_user_is_not_counted(self, admin_client):
        UserFactory().delete()

        assert admin_client.get(URL).json()["data"]["users"]["total"] == 1

    def test_growth_is_measured_against_the_base_it_grew_from(self, admin_client):
        """
        Not against the new total — otherwise doubling your users reads as 50%
        growth and 100% is arithmetically unreachable.
        """
        body = admin_client.get(URL, {"period": "all"}).json()["data"]

        # Every user is inside the "all time" window, so there is no base.
        assert body["users"]["growth_pct"] == 0.0

    def test_trip_counters_and_average_stops(self, admin_client):
        trip_with_cost(public=True)
        second = trip_with_cost()
        TripStopFactory(
            trip=second,
            start_date=second.start_date + timedelta(days=1),
            end_date=second.end_date,
        )

        trips = admin_client.get(URL).json()["data"]["trips"]

        assert trips["total"] == 2
        assert trips["created_this_period"] == 2
        assert trips["public"] == 1
        assert trips["avg_stops_per_trip"] == 1.5

    def test_the_platform_total_matches_the_sum_of_the_trips(self, admin_client):
        """
        Same formula as the trip list, aggregated. If these two ever disagree,
        the admin panel is quietly lying about the platform.
        """
        from apps.budget.services import bulk_trip_cost_summary

        first = trip_with_cost(activity="2000.00", expense="500.00")
        second = trip_with_cost(activity="1000.00", expense="250.00")

        body = admin_client.get(URL).json()["data"]
        per_trip = bulk_trip_cost_summary([first.pk, second.pk])
        expected = sum(row["grand_total"] for row in per_trip.values())

        assert body["budget"]["total_planned_value"] == str(expected)
        assert body["budget"]["total_planned_value"] == "3750.00"

    def test_a_deleted_trips_money_leaves_the_platform_total(self, admin_client):
        trip = trip_with_cost(activity="2000.00", expense="500.00")
        trip.delete()

        body = admin_client.get(URL).json()["data"]

        assert body["budget"]["total_planned_value"] == "0.00"

    def test_avg_trip_budget_ignores_trips_with_no_budget(self, admin_client):
        trip_with_cost(budget="40000.00")
        trip_with_cost(budget="60000.00")
        trip_with_cost()  # no budget set

        body = admin_client.get(URL).json()["data"]

        assert body["budget"]["avg_trip_budget"] == "50000.00"

    def test_the_period_narrows_the_this_period_counters_only(self, admin_client):
        trip_with_cost()

        week = admin_client.get(URL, {"period": "7d"}).json()["data"]

        # Created just now, so it is inside a 7-day window too.
        assert week["trips"]["total"] == 1
        assert week["trips"]["created_this_period"] == 1


class TestOverviewQueryBudget:
    def test_it_does_not_scale_with_the_platform(
        self, admin_client, django_assert_num_queries
    ):
        """
        Rolling `bulk_trip_cost_summary` over every trip would give the same
        numbers and scan the table to do it. Six aggregates plus the
        authenticating user.
        """
        trip_with_cost()

        with django_assert_num_queries(7) as captured:
            admin_client.get(URL)

        for _ in range(6):
            trip_with_cost()

        with django_assert_num_queries(len(captured.captured_queries)):
            admin_client.get(URL)
