"""trips — the admin moderation tree (task B6.3)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, AdminFactory, UserFactory
from apps.budget.tests.factories import ExpenseFactory
from apps.trips.constants import TripStatus
from apps.trips.models import Trip
from apps.trips.tests.factories import TripActivityFactory, TripFactory, TripStopFactory

pytestmark = pytest.mark.django_db

TODAY = date.today()
LIST_URL = reverse("admin-trip-list")


def detail_url(trip_id) -> str:
    return reverse("admin-trip-detail", args=[trip_id])


@pytest.fixture
def client():
    admin = AdminFactory(email="admin@globetrotter.dev")
    api = APIClient()
    response = api.post(
        reverse("auth-login"),
        {"email": admin.email, "password": DEFAULT_PASSWORD},
        format="json",
    )
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['tokens']['access']}")
    return api


def trip_with_content(user, *, cost="2000.00", expense="500.00", public=False):
    trip = TripFactory(
        user=user,
        start_date=TODAY + timedelta(days=10),
        end_date=TODAY + timedelta(days=14),
        total_budget=Decimal("50000.00"),
        is_public=public,
    )
    stop = TripStopFactory(trip=trip, start_date=trip.start_date, end_date=trip.end_date)
    TripActivityFactory(trip_stop=stop, day_date=trip.start_date, cost=Decimal(cost))
    ExpenseFactory(trip=trip, amount=Decimal(expense), incurred_on=trip.start_date)
    return trip


class TestAdminTripList:
    def test_it_shows_every_users_trips(self, client):
        """The one list in the project that is not owner-scoped."""
        first = trip_with_content(UserFactory(email="a@example.com"))
        second = trip_with_content(UserFactory(email="b@example.com"))

        body = client.get(LIST_URL).json()

        assert {row["id"] for row in body["data"]["results"]} == {first.pk, second.pk}

    def test_the_row_carries_the_owner_and_the_real_cost(self, client):
        user = UserFactory(email="riya@example.com")
        trip = trip_with_content(user, cost="2000.00", expense="500.00")

        row = client.get(LIST_URL).json()["data"]["results"][0]

        assert row["id"] == trip.pk
        assert row["user_id"] == user.pk
        assert row["user_email"] == "riya@example.com"
        # Same formula as the user's own list — the two must not disagree.
        assert row["estimated_cost"] == "2500.00"
        assert row["stops_count"] == 1
        assert row["activities_count"] == 1
        assert row["is_deleted"] is False

    def test_it_filters_by_owner(self, client):
        mine = trip_with_content(UserFactory(email="a@example.com"))
        trip_with_content(UserFactory(email="b@example.com"))

        body = client.get(LIST_URL, {"user": mine.user_id}).json()

        assert [row["id"] for row in body["data"]["results"]] == [mine.pk]

    def test_it_filters_by_status_and_visibility(self, client):
        user = UserFactory()
        public = trip_with_content(user, public=True)
        trip_with_content(user)

        body = client.get(LIST_URL, {"is_public": "true"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [public.pk]
        assert (
            client.get(LIST_URL, {"status": TripStatus.PLANNED}).json()["data"]["pagination"][
                "count"
            ]
            == 2
        )

    def test_it_searches_by_owner_email(self, client):
        match = trip_with_content(UserFactory(email="riya@example.com"))
        trip_with_content(UserFactory(email="other@example.com"))

        body = client.get(LIST_URL, {"search": "riya"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [match.pk]

    def test_deleted_trips_are_hidden_unless_asked_for(self, client):
        trip = trip_with_content(UserFactory())
        trip.delete()

        assert client.get(LIST_URL).json()["data"]["pagination"]["count"] == 0
        with_deleted = client.get(LIST_URL, {"include_deleted": "true"}).json()
        assert [row["id"] for row in with_deleted["data"]["results"]] == [trip.pk]
        assert with_deleted["data"]["results"][0]["is_deleted"] is True

    def test_query_count_does_not_grow_with_the_page(self, client, django_assert_num_queries):
        """The moderation table is the widest list in the project — trap #9."""
        user = UserFactory()
        for _ in range(2):
            trip_with_content(user)

        with django_assert_num_queries(7) as captured:
            client.get(LIST_URL)

        for _ in range(8):
            trip_with_content(user)

        with django_assert_num_queries(len(captured.captured_queries)):
            client.get(LIST_URL)


class TestAdminTripDetail:
    def test_it_reads_any_trip(self, client):
        trip = trip_with_content(UserFactory(email="riya@example.com"))

        body = client.get(detail_url(trip.pk)).json()["data"]

        assert body["id"] == trip.pk
        assert body["user_email"] == "riya@example.com"
        assert body["estimated_cost"] == "2500.00"

    def test_delete_is_soft(self, client):
        trip = trip_with_content(UserFactory())

        response = client.delete(detail_url(trip.pk))

        assert response.status_code == 204
        assert not Trip.objects.filter(pk=trip.pk).exists()
        assert Trip.all_objects.filter(pk=trip.pk).exists()

    def test_a_deleted_trip_stays_addressable_by_id(self, client):
        trip = trip_with_content(UserFactory())
        client.delete(detail_url(trip.pk))

        assert client.get(detail_url(trip.pk)).status_code == 200

    def test_a_moderator_cannot_rewrite_the_itinerary(self, client):
        """Moderation removes a trip; it does not edit somebody's plan."""
        trip = trip_with_content(UserFactory())

        response = client.patch(detail_url(trip.pk), {"name": "Rewritten"}, format="json")

        assert response.status_code == 405
        trip.refresh_from_db()
        assert trip.name != "Rewritten"


class TestAdminUserTrips:
    def test_it_lists_one_users_trips(self, client):
        user = UserFactory(email="riya@example.com")
        mine = trip_with_content(user)
        trip_with_content(UserFactory())

        body = client.get(reverse("admin-user-trips", args=[user.pk])).json()

        assert [row["id"] for row in body["data"]["results"]] == [mine.pk]

    def test_an_unknown_user_is_an_empty_list_not_a_404(self, client):
        """It is a filtered list, not a nested detail route."""
        body = client.get(reverse("admin-user-trips", args=[999999])).json()

        assert body["data"]["pagination"]["count"] == 0

    def test_it_can_still_be_filtered(self, client):
        user = UserFactory()
        public = trip_with_content(user, public=True)
        trip_with_content(user)

        body = client.get(
            reverse("admin-user-trips", args=[user.pk]), {"is_public": "true"}
        ).json()

        assert [row["id"] for row in body["data"]["results"]] == [public.pk]
