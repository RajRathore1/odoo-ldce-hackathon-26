"""
trips — sharing and copy (task A7).

Its own module because two of these tests guard rules that are easy to break by
accident and expensive to break in public: **no PII on the public page**, and
**no off-by-one in the date rebase**.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, UserFactory
from apps.budget.tests.factories import ExpenseFactory
from apps.geo.tests.factories import CityFactory
from apps.trips.constants import TripStatus
from apps.trips.models import Trip, TripActivity, TripStop
from apps.trips.tests.factories import TripActivityFactory, TripFactory, TripStopFactory

pytestmark = pytest.mark.django_db

TODAY = date.today()


def authenticated(user) -> APIClient:
    api = APIClient()
    response = api.post(
        reverse("auth-login"),
        {"email": user.email, "password": DEFAULT_PASSWORD},
        format="json",
    )
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['tokens']['access']}")
    return api


@pytest.fixture
def owner():
    return UserFactory(
        email="riya@example.com",
        first_name="Riya",
        last_name="Sharma",
        phone_number="+91 98250 11111",
    )


@pytest.fixture
def client(owner):
    return authenticated(owner)


@pytest.fixture
def trip(owner):
    """A ten-day trip with two stops, three activities and two expenses."""
    trip = TripFactory(
        user=owner,
        name="Himachal Winter",
        description="Bir and Manali",
        start_date=TODAY + timedelta(days=30),
        end_date=TODAY + timedelta(days=39),
        total_budget=Decimal("50000.00"),
    )
    first = TripStopFactory(
        trip=trip,
        order=1,
        city=CityFactory(name="Bir"),
        start_date=trip.start_date,
        end_date=trip.start_date + timedelta(days=3),
        budget=Decimal("18000.00"),
    )
    second = TripStopFactory(
        trip=trip,
        order=2,
        city=CityFactory(name="Manali"),
        start_date=trip.start_date + timedelta(days=4),
        end_date=trip.start_date + timedelta(days=7),
    )
    TripActivityFactory(
        trip_stop=first,
        custom_title="Paragliding",
        day_date=first.start_date,
        cost=Decimal("2500.00"),
        order=1,
    )
    TripActivityFactory(
        trip_stop=first,
        custom_title="Monastery walk",
        day_date=first.start_date + timedelta(days=1),
        cost=Decimal("600.00"),
        order=1,
    )
    TripActivityFactory(
        trip_stop=second,
        custom_title="Solang ropeway",
        day_date=second.start_date,
        cost=Decimal("1800.00"),
        order=1,
    )
    ExpenseFactory(trip=trip, amount=Decimal("14000.00"), incurred_on=trip.start_date)
    ExpenseFactory(trip=trip, trip_stop=first, amount=Decimal("3000.00"), incurred_on=None)
    return trip


def share_url(trip_id) -> str:
    return reverse("trip-share", args=[trip_id])


def public_url(token) -> str:
    return reverse("public-trip", args=[token])


def copy_url(token) -> str:
    return reverse("public-trip-copy", args=[token])


# ---------------------------------------------------------------------- share


class TestShare:
    def test_post_publishes_the_trip(self, client, trip):
        response = client.post(share_url(trip.pk))
        body = response.json()

        assert response.status_code == 200
        assert body["message"] == "Trip is now public."
        assert body["data"]["is_public"] is True
        assert body["data"]["share_token"] == str(trip.share_token)
        assert body["data"]["share_url"].endswith(f"/trips/shared/{trip.share_token}")
        trip.refresh_from_db()
        assert trip.is_public is True

    def test_delete_revokes_but_keeps_the_link(self, client, trip):
        """Re-sharing must give back the same URL — people paste these in chats."""
        client.post(share_url(trip.pk))
        token = trip.share_token

        response = client.delete(share_url(trip.pk))

        assert response.status_code == 200
        assert response.json()["message"] == "Sharing revoked."
        trip.refresh_from_db()
        assert trip.is_public is False
        assert trip.share_token == token

    def test_regenerate_kills_the_old_link(self, client, trip):
        client.post(share_url(trip.pk))
        old_token = trip.share_token

        response = client.post(reverse("trip-share-regenerate", args=[trip.pk]))

        assert response.status_code == 200
        trip.refresh_from_db()
        assert trip.share_token != old_token
        assert APIClient().get(public_url(old_token)).status_code == 404

    def test_cannot_share_somebody_elses_trip(self, client):
        stranger = TripFactory(user=UserFactory())

        assert client.post(share_url(stranger.pk)).status_code == 404
        stranger.refresh_from_db()
        assert stranger.is_public is False


# --------------------------------------------------------------- public page


class TestPublicTrip:
    def test_a_private_trip_is_a_404(self, trip):
        assert APIClient().get(public_url(trip.share_token)).status_code == 404

    def test_an_unknown_token_is_a_404(self):
        assert APIClient().get(public_url(uuid.uuid4())).status_code == 404

    def test_a_deleted_trip_is_a_404(self, client, trip):
        client.post(share_url(trip.pk))
        trip.delete()

        assert APIClient().get(public_url(trip.share_token)).status_code == 404

    def test_it_needs_no_login(self, client, trip):
        client.post(share_url(trip.pk))

        assert APIClient().get(public_url(trip.share_token)).status_code == 200

    def test_it_carries_the_whole_itinerary(self, client, trip):
        client.post(share_url(trip.pk))

        body = APIClient().get(public_url(trip.share_token)).json()["data"]

        assert body["trip"]["name"] == "Himachal Winter"
        assert body["trip"]["duration_days"] == 10
        assert len(body["days"]) == 10
        assert body["days"][0]["activities"][0]["title"] == "Paragliding"
        assert body["totals"]["grand_total"] == "21900.00"

    def test_no_pii_reaches_the_public_payload(self, client, trip, owner):
        """
        Trap #7. The owner is reduced to a first name and an avatar — asserted
        against the serialised text, so a future nested serializer that quietly
        adds a field fails here rather than in front of the internet.
        """
        client.post(share_url(trip.pk))

        response = APIClient().get(public_url(trip.share_token))
        raw = response.content.decode()
        body = response.json()["data"]

        assert body["owner"] == {"first_name": "Riya", "avatar": None}
        # The owner's own id is not exposed either — checked as a key rather
        # than a substring, since a bare "1" appears in every id and date.
        assert "id" not in body["owner"]
        for private in (owner.email, "Sharma", "+91 98250 11111", "phone_number"):
            assert private not in raw, private

    def test_no_budget_target_reaches_the_public_payload(self, client, trip):
        """
        `total_budget` and `remaining` are financial targets, not trip content.
        `grand_total` stays: what a trip costs is the point of sharing it.
        """
        client.post(share_url(trip.pk))

        response = APIClient().get(public_url(trip.share_token))
        body = response.json()["data"]

        assert "total_budget" not in body
        assert "total_budget" not in body["trip"]
        assert "remaining" not in body["totals"]
        assert "50000" not in response.content.decode()
        assert body["totals"]["grand_total"] == "21900.00"

    def test_it_counts_views(self, client, trip):
        client.post(share_url(trip.pk))
        anonymous = APIClient()

        first = anonymous.get(public_url(trip.share_token)).json()["data"]
        anonymous.get(public_url(trip.share_token))

        assert first["views_count"] == 1
        trip.refresh_from_db()
        assert trip.views_count == 2


# ----------------------------------------------------------------------- copy


class TestCopyTrip:
    @pytest.fixture
    def shared(self, client, trip):
        client.post(share_url(trip.pk))
        return trip

    @pytest.fixture
    def copier(self):
        return UserFactory(email="copier@example.com")

    def test_it_needs_a_login(self, shared):
        assert APIClient().post(copy_url(shared.share_token)).status_code == 401

    def test_it_deep_copies_the_whole_trip(self, shared, copier):
        response = authenticated(copier).post(copy_url(shared.share_token), {}, format="json")
        body = response.json()

        assert response.status_code == 201
        assert body["message"] == "Trip copied to your account."

        copy = Trip.objects.get(pk=body["data"]["id"])
        assert copy.user == copier
        assert copy.copied_from_id == shared.pk
        assert TripStop.objects.filter(trip=copy).count() == 2
        assert TripActivity.objects.filter(trip_stop__trip=copy).count() == 3
        assert copy.expenses.count() == 2

    def test_the_copy_is_private_a_draft_and_has_its_own_link(self, shared, copier):
        body = authenticated(copier).post(copy_url(shared.share_token), {}, format="json")

        copy = Trip.objects.get(pk=body.json()["data"]["id"])
        assert copy.is_public is False
        assert copy.status == TripStatus.DRAFT
        assert copy.share_token != shared.share_token
        assert copy.views_count == 0

    def test_the_original_is_untouched(self, shared, copier):
        authenticated(copier).post(copy_url(shared.share_token), {}, format="json")

        shared.refresh_from_db()
        assert shared.user != copier
        assert shared.is_public is True
        assert TripStop.objects.filter(trip=shared).count() == 2

    def test_dates_are_rebased_onto_the_new_start_with_no_off_by_one(self, shared, copier):
        """
        A7.4. Day one lands exactly on `start_date`, the trip keeps its length,
        and every child moves by the same offset — a rebase that drifts by a day
        puts an activity outside its own stop and breaks the itinerary.
        """
        new_start = TODAY + timedelta(days=200)

        body = authenticated(copier).post(
            copy_url(shared.share_token), {"start_date": str(new_start)}, format="json"
        )

        copy = Trip.objects.get(pk=body.json()["data"]["id"])
        offset = (new_start - shared.start_date).days

        assert copy.start_date == new_start
        assert copy.duration_days == shared.duration_days
        assert copy.end_date == shared.end_date + timedelta(days=offset)

        source_stops = list(TripStop.objects.filter(trip=shared).order_by("order"))
        copy_stops = list(TripStop.objects.filter(trip=copy).order_by("order"))
        for source, copied in zip(source_stops, copy_stops, strict=True):
            assert copied.start_date == source.start_date + timedelta(days=offset)
            assert copied.end_date == source.end_date + timedelta(days=offset)
            assert copied.city_id == source.city_id
            assert copied.order == source.order

        for activity in TripActivity.objects.filter(trip_stop__trip=copy).select_related(
            "trip_stop"
        ):
            stop = activity.trip_stop
            assert stop.start_date <= activity.day_date <= stop.end_date

    def test_every_copied_day_falls_inside_the_copied_trip(self, shared, copier):
        """The itinerary only emits dates in range, so a strays day would vanish."""
        body = authenticated(copier).post(
            copy_url(shared.share_token),
            {"start_date": str(TODAY + timedelta(days=90))},
            format="json",
        )

        copy = Trip.objects.get(pk=body.json()["data"]["id"])
        for stop in TripStop.objects.filter(trip=copy):
            assert copy.start_date <= stop.start_date
            assert stop.end_date <= copy.end_date

    def test_omitting_a_start_date_keeps_the_original_dates(self, shared, copier):
        body = authenticated(copier).post(copy_url(shared.share_token), {}, format="json")

        copy = Trip.objects.get(pk=body.json()["data"]["id"])
        assert copy.start_date == shared.start_date
        assert copy.end_date == shared.end_date

    def test_an_expense_with_no_day_stays_dayless(self, shared, copier):
        body = authenticated(copier).post(
            copy_url(shared.share_token),
            {"start_date": str(TODAY + timedelta(days=90))},
            format="json",
        )

        copy = Trip.objects.get(pk=body.json()["data"]["id"])
        assert copy.expenses.filter(incurred_on__isnull=True).count() == 1

    def test_the_name_can_be_overridden(self, shared, copier):
        body = authenticated(copier).post(
            copy_url(shared.share_token), {"name": "My Himachal Trip"}, format="json"
        )

        assert body.json()["data"]["name"] == "My Himachal Trip"

    def test_the_cost_snapshot_travels_with_the_copy(self, shared, copier):
        """Re-reading the catalog here would silently reprice somebody's plan."""
        body = authenticated(copier).post(copy_url(shared.share_token), {}, format="json")

        copy = Trip.objects.get(pk=body.json()["data"]["id"])
        assert sorted(
            TripActivity.objects.filter(trip_stop__trip=copy).values_list("cost", flat=True)
        ) == sorted(
            TripActivity.objects.filter(trip_stop__trip=shared).values_list("cost", flat=True)
        )

    def test_the_copy_costs_the_same_as_the_original(self, shared, copier):
        from apps.budget.services import trip_cost_summary

        body = authenticated(copier).post(copy_url(shared.share_token), {}, format="json")

        copy = Trip.objects.get(pk=body.json()["data"]["id"])
        assert (
            trip_cost_summary(copy)["grand_total"] == trip_cost_summary(shared)["grand_total"]
        )

    def test_a_private_trip_cannot_be_copied(self, trip, copier):
        assert (
            authenticated(copier)
            .post(copy_url(trip.share_token), {}, format="json")
            .status_code
            == 404
        )

    def test_copying_bumps_the_city_counters(self, shared, copier):
        """A copy adds real stops, so `/cities/popular/` should notice."""
        before = {
            stop.city_id: stop.city.popularity_score
            for stop in TripStop.objects.filter(trip=shared).select_related("city")
        }

        authenticated(copier).post(copy_url(shared.share_token), {}, format="json")

        for city_id, score in before.items():
            stop = TripStop.objects.filter(city_id=city_id).first()
            stop.city.refresh_from_db()
            assert stop.city.popularity_score == score + 1
