"""trips — status codes, envelope shape, permissions."""

import io
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, UserFactory
from apps.activities.constants import ActivityType
from apps.activities.tests.factories import ActivityFactory
from apps.geo.tests.factories import CityFactory
from apps.trips.constants import TripStatus
from apps.trips.models import Trip, TripActivity, TripStop
from apps.trips.tests.factories import (
    TripActivityFactory,
    TripFactory,
    TripStopFactory,
)

pytestmark = pytest.mark.django_db

TODAY = date.today()
LIST_URL = reverse("trip-list")


def detail_url(trip_id) -> str:
    return reverse("trip-detail", args=[trip_id])


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


def png_bytes() -> io.BytesIO:
    """A real 1x1 PNG — `ImageField` validation rejects arbitrary bytes."""
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1)).save(buffer, format="PNG")
    buffer.seek(0)
    buffer.name = "cover.png"
    return buffer


def payload(**overrides) -> dict:
    data = {
        "name": "Europe Summer",
        "description": "Three cities, two weeks",
        "start_date": str(TODAY + timedelta(days=60)),
        "end_date": str(TODAY + timedelta(days=74)),
        "total_budget": "50000.00",
        "currency": "INR",
    }
    return {**data, **overrides}


# ----------------------------------------------------------------------- list


class TestTripList:
    def test_requires_authentication(self):
        assert APIClient().get(LIST_URL).status_code == 401

    def test_returns_only_my_trips(self, client, user, other_user):
        mine = TripFactory(user=user, name="Mine")
        TripFactory(user=other_user, name="Theirs")

        body = client.get(LIST_URL).json()

        assert [row["id"] for row in body["data"]["results"]] == [mine.pk]

    def test_envelope_and_pagination_shape(self, client, user):
        TripFactory(user=user)

        response = client.get(LIST_URL)
        body = response.json()

        assert response.status_code == 200
        assert body["success"] is True
        assert body["message"] is None
        assert body["data"]["pagination"]["count"] == 1
        assert body["data"]["pagination"]["page"] == 1
        assert body["data"]["pagination"]["has_next"] is False

    def test_row_carries_the_flat_aggregates(self, client, user):
        trip = TripFactory(user=user, total_budget="50000.00")

        row = client.get(LIST_URL).json()["data"]["results"][0]

        assert row["duration_days"] == 8
        assert row["stops_count"] == 0
        assert row["activities_count"] == 0
        assert row["cities"] == []
        assert row["total_budget"] == "50000.00"
        # Zero until A6 wires bulk_trip_cost_summary — the shape is final.
        assert row["estimated_cost"] == "0.00"
        assert row["is_over_budget"] is False
        assert row["share_url"].endswith(f"/trips/shared/{trip.share_token}")

    def test_share_token_is_not_exposed_on_a_list_row(self, client, user):
        TripFactory(user=user)
        assert "share_token" not in client.get(LIST_URL).json()["data"]["results"][0]

    def test_soft_deleted_trips_are_hidden(self, client, user):
        TripFactory(user=user).delete()
        assert client.get(LIST_URL).json()["data"]["pagination"]["count"] == 0

    def test_query_count_does_not_grow_with_the_page(
        self, client, user, django_assert_num_queries
    ):
        """
        Trap #9. The list must be flat, whatever the page size.

        Four: the authenticating user, the page count, the page itself, and one
        prefetch for every stop on it.
        """
        TripFactory.create_batch(3, user=user)
        with django_assert_num_queries(4) as captured:
            client.get(LIST_URL)

        TripFactory.create_batch(12, user=user)
        with django_assert_num_queries(len(captured.captured_queries)):
            client.get(LIST_URL)


class TestTripListFilters:
    def test_filters_by_status(self, client, user):
        TripFactory(
            user=user,
            start_date=TODAY - timedelta(days=9),
            end_date=TODAY - timedelta(days=2),
        )
        ongoing = TripFactory(
            user=user,
            start_date=TODAY - timedelta(days=1),
            end_date=TODAY + timedelta(days=1),
        )

        body = client.get(LIST_URL, {"status": "ONGOING"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [ongoing.pk]

    def test_status_accepts_several_tabs_at_once(self, client, user):
        TripFactory(
            user=user,
            start_date=TODAY - timedelta(days=9),
            end_date=TODAY - timedelta(days=2),
        )
        TripFactory(user=user, status=TripStatus.DRAFT)
        TripFactory(user=user)  # PLANNED

        body = client.get(LIST_URL, {"status": "DRAFT,COMPLETED"}).json()

        assert body["data"]["pagination"]["count"] == 2

    def test_search_covers_name_and_description(self, client, user):
        match = TripFactory(user=user, name="Himachal Winter")
        TripFactory(user=user, name="Kerala Backwaters", description="houseboat")

        body = client.get(LIST_URL, {"search": "himachal"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [match.pk]

    def test_filters_by_start_date_bounds(self, client, user):
        early = TripFactory(
            user=user,
            start_date=TODAY + timedelta(days=5),
            end_date=TODAY + timedelta(days=9),
        )
        TripFactory(
            user=user,
            start_date=TODAY + timedelta(days=90),
            end_date=TODAY + timedelta(days=95),
        )

        body = client.get(
            LIST_URL, {"start_date_before": str(TODAY + timedelta(days=30))}
        ).json()

        assert [row["id"] for row in body["data"]["results"]] == [early.pk]

    def test_ordering_by_start_date(self, client, user):
        later = TripFactory(
            user=user,
            start_date=TODAY + timedelta(days=90),
            end_date=TODAY + timedelta(days=95),
        )
        sooner = TripFactory(
            user=user,
            start_date=TODAY + timedelta(days=5),
            end_date=TODAY + timedelta(days=9),
        )

        body = client.get(LIST_URL, {"ordering": "start_date"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [sooner.pk, later.pk]


# --------------------------------------------------------------------- create


class TestTripCreate:
    def test_creates_a_trip_for_the_caller(self, client, user):
        response = client.post(LIST_URL, payload(), format="json")
        body = response.json()

        assert response.status_code == 201
        assert body["message"] == "Trip created successfully."
        assert body["data"]["name"] == "Europe Summer"
        assert body["data"]["duration_days"] == 15
        assert body["data"]["status"] == TripStatus.PLANNED
        assert body["data"]["stops_count"] == 0
        assert body["data"]["is_public"] is False
        assert body["data"]["share_token"]
        assert Trip.objects.get().user == user

    def test_cannot_create_a_trip_for_somebody_else(self, client, user, other_user):
        client.post(LIST_URL, payload(user=other_user.pk), format="json")
        assert Trip.objects.get().user == user

    def test_end_date_before_start_date_is_rejected(self, client):
        response = client.post(
            LIST_URL,
            payload(start_date=str(TODAY + timedelta(days=10)), end_date=str(TODAY)),
            format="json",
        )

        assert response.status_code == 400
        assert "end_date" in response.json()["errors"]["fields"]

    def test_a_past_trip_is_allowed_and_lands_completed(self, client):
        """Users log trips they have already taken."""
        response = client.post(
            LIST_URL,
            payload(
                start_date=str(TODAY - timedelta(days=20)),
                end_date=str(TODAY - timedelta(days=10)),
            ),
            format="json",
        )

        assert response.status_code == 201
        assert response.json()["data"]["status"] == TripStatus.COMPLETED

    def test_draft_survives_the_status_sync(self, client):
        response = client.post(LIST_URL, payload(status=TripStatus.DRAFT), format="json")
        assert response.json()["data"]["status"] == TripStatus.DRAFT

    def test_currency_is_normalised_to_upper_case(self, client):
        client.post(LIST_URL, payload(currency="inr"), format="json")
        assert Trip.objects.get().currency == "INR"

    def test_total_budget_is_optional(self, client):
        response = client.post(LIST_URL, payload(total_budget=None), format="json")
        assert response.status_code == 201
        assert response.json()["data"]["total_budget"] is None

    def test_missing_name_is_a_field_error(self, client):
        response = client.post(LIST_URL, payload(name=""), format="json")
        assert response.status_code == 400
        assert "name" in response.json()["errors"]["fields"]


# ------------------------------------------------------------- detail / update


class TestTripDetail:
    def test_owner_reads_the_detail_shape(self, client, user):
        trip = TripFactory(user=user)

        response = client.get(detail_url(trip.pk))
        body = response.json()

        assert response.status_code == 200
        assert body["data"]["id"] == trip.pk
        assert body["data"]["share_token"] == str(trip.share_token)
        assert body["data"]["views_count"] == 0

    def test_somebody_elses_trip_is_a_404_not_a_403(self, client, other_user):
        """The queryset is owner-scoped, so a stranger's id does not exist."""
        trip = TripFactory(user=other_user)
        assert client.get(detail_url(trip.pk)).status_code == 404

    def test_patch_updates_the_trip(self, client, user):
        trip = TripFactory(user=user)

        response = client.patch(
            detail_url(trip.pk),
            {"name": "Renamed", "total_budget": "1200.50"},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Trip updated."
        trip.refresh_from_db()
        assert trip.name == "Renamed"
        assert str(trip.total_budget) == "1200.50"

    def test_patching_one_date_is_validated_against_the_stored_other_one(self, client, user):
        trip = TripFactory(
            user=user,
            start_date=TODAY + timedelta(days=10),
            end_date=TODAY + timedelta(days=20),
        )

        response = client.patch(
            detail_url(trip.pk),
            {"end_date": str(TODAY + timedelta(days=5))},
            format="json",
        )

        assert response.status_code == 400
        assert "end_date" in response.json()["errors"]["fields"]

    def test_is_public_cannot_be_set_by_patch(self, client, user):
        """Sharing has its own endpoints (A7); this must not be a second door."""
        trip = TripFactory(user=user)

        client.patch(detail_url(trip.pk), {"is_public": True}, format="json")

        trip.refresh_from_db()
        assert trip.is_public is False

    def test_cancelling_a_trip_sticks(self, client, user):
        trip = TripFactory(user=user)

        response = client.patch(
            detail_url(trip.pk), {"status": TripStatus.CANCELLED}, format="json"
        )

        assert response.json()["data"]["status"] == TripStatus.CANCELLED
        trip.refresh_from_db()
        assert trip.status == TripStatus.CANCELLED

    def test_cannot_patch_somebody_elses_trip(self, client, other_user):
        trip = TripFactory(user=other_user, name="Theirs")

        response = client.patch(detail_url(trip.pk), {"name": "Hijacked"}, format="json")

        assert response.status_code == 404
        trip.refresh_from_db()
        assert trip.name == "Theirs"


class TestTripDelete:
    def test_delete_soft_deletes_and_returns_204(self, client, user):
        trip = TripFactory(user=user)

        response = client.delete(detail_url(trip.pk))

        assert response.status_code == 204
        assert not Trip.objects.filter(pk=trip.pk).exists()
        assert Trip.all_objects.filter(pk=trip.pk).exists()

    def test_a_deleted_trip_is_gone_from_the_api(self, client, user):
        trip = TripFactory(user=user)
        client.delete(detail_url(trip.pk))
        assert client.get(detail_url(trip.pk)).status_code == 404

    def test_cannot_delete_somebody_elses_trip(self, client, other_user):
        trip = TripFactory(user=other_user)
        assert client.delete(detail_url(trip.pk)).status_code == 404
        assert Trip.objects.filter(pk=trip.pk).exists()


class TestCoverPhoto:
    def url(self, trip_id) -> str:
        return reverse("trip-cover-photo", args=[trip_id])

    def test_upload_sets_the_cover_photo(self, client, user, tmp_path, settings):
        settings.MEDIA_ROOT = tmp_path
        trip = TripFactory(user=user)

        response = client.post(
            self.url(trip.pk), {"cover_photo": png_bytes()}, format="multipart"
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Cover photo updated."
        trip.refresh_from_db()
        assert trip.cover_photo.name.startswith("trips/covers/")

    def test_a_non_image_is_rejected(self, client, user, tmp_path, settings):
        settings.MEDIA_ROOT = tmp_path
        trip = TripFactory(user=user)

        response = client.post(
            self.url(trip.pk),
            {"cover_photo": io.BytesIO(b"not an image")},
            format="multipart",
        )

        assert response.status_code == 400

    def test_cannot_upload_to_somebody_elses_trip(
        self, client, other_user, tmp_path, settings
    ):
        settings.MEDIA_ROOT = tmp_path
        trip = TripFactory(user=other_user)

        response = client.post(
            self.url(trip.pk), {"cover_photo": png_bytes()}, format="multipart"
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------- stops


@pytest.fixture
def trip(user):
    """A ten-day trip, so a stop always has room to sit inside it."""
    return TripFactory(
        user=user,
        start_date=TODAY + timedelta(days=30),
        end_date=TODAY + timedelta(days=39),
    )


def stops_url(trip_id) -> str:
    return reverse("trip-stop-list", args=[trip_id])


def stop_detail_url(trip_id, stop_id) -> str:
    return reverse("trip-stop-detail", args=[trip_id, stop_id])


def stop_payload(trip, **overrides) -> dict:
    data = {
        "city": CityFactory().pk,
        "start_date": str(trip.start_date),
        "end_date": str(trip.start_date + timedelta(days=3)),
        "budget": "18000.00",
    }
    return {**data, **overrides}


class TestStopCreate:
    def test_creates_a_stop_and_returns_the_nested_city(self, client, trip):
        city = CityFactory(name="Bir")

        response = client.post(
            stops_url(trip.pk), stop_payload(trip, city=city.pk), format="json"
        )
        body = response.json()

        assert response.status_code == 201
        assert body["message"] == "Stop added."
        assert body["data"]["title"] == "Bir"
        assert body["data"]["city"]["id"] == city.pk
        assert body["data"]["city"]["country_name"] == city.country.name
        assert body["data"]["nights"] == 3
        assert body["data"]["order"] == 1
        assert body["data"]["activities_count"] == 0

    def test_order_is_assigned_server_side_and_ignores_the_client(self, client, trip):
        client.post(stops_url(trip.pk), stop_payload(trip, order=99), format="json")
        second = client.post(
            stops_url(trip.pk),
            stop_payload(
                trip,
                start_date=str(trip.start_date + timedelta(days=4)),
                end_date=str(trip.start_date + timedelta(days=6)),
                order=99,
            ),
            format="json",
        )

        assert [stop.order for stop in TripStop.objects.filter(trip=trip)] == [1, 2]
        assert second.json()["data"]["order"] == 2

    def test_a_stop_starting_before_the_trip_is_rejected(self, client, trip):
        response = client.post(
            stops_url(trip.pk),
            stop_payload(trip, start_date=str(trip.start_date - timedelta(days=1))),
            format="json",
        )

        assert response.status_code == 400
        assert "start_date" in response.json()["errors"]["fields"]

    def test_a_stop_ending_after_the_trip_is_rejected(self, client, trip):
        response = client.post(
            stops_url(trip.pk),
            stop_payload(trip, end_date=str(trip.end_date + timedelta(days=1))),
            format="json",
        )

        assert response.status_code == 400
        assert "start_date" in response.json()["errors"]["fields"]

    def test_end_before_start_is_rejected(self, client, trip):
        response = client.post(
            stops_url(trip.pk),
            stop_payload(trip, end_date=str(trip.start_date - timedelta(days=1))),
            format="json",
        )

        assert response.status_code == 400
        assert "end_date" in response.json()["errors"]["fields"]

    def test_cannot_add_a_stop_to_somebody_elses_trip(self, client, other_user):
        stranger = TripFactory(user=other_user)

        response = client.post(stops_url(stranger.pk), stop_payload(stranger), format="json")

        assert response.status_code == 404
        assert not TripStop.objects.exists()


class TestStopList:
    def test_lists_the_trips_stops_in_order(self, client, trip):
        second = TripStopFactory(
            trip=trip,
            order=2,
            start_date=trip.start_date + timedelta(days=4),
            end_date=trip.start_date + timedelta(days=5),
        )
        first = TripStopFactory(
            trip=trip,
            order=1,
            start_date=trip.start_date,
            end_date=trip.start_date + timedelta(days=2),
        )

        body = client.get(stops_url(trip.pk)).json()

        assert [row["id"] for row in body["data"]["results"]] == [first.pk, second.pk]

    def test_activities_count_is_annotated(self, client, trip):
        stop = TripStopFactory(
            trip=trip, start_date=trip.start_date, end_date=trip.start_date + timedelta(days=2)
        )
        TripActivityFactory.create_batch(2, trip_stop=stop, day_date=trip.start_date)

        body = client.get(stops_url(trip.pk)).json()

        assert body["data"]["results"][0]["activities_count"] == 2

    def test_a_deleted_stop_is_hidden(self, client, trip):
        TripStopFactory(
            trip=trip, start_date=trip.start_date, end_date=trip.start_date + timedelta(days=1)
        ).delete()

        assert client.get(stops_url(trip.pk)).json()["data"]["pagination"]["count"] == 0


class TestStopDetail:
    @pytest.fixture
    def stop(self, trip):
        return TripStopFactory(
            trip=trip, start_date=trip.start_date, end_date=trip.start_date + timedelta(days=2)
        )

    def test_patch_updates_the_stop(self, client, trip, stop):
        response = client.patch(
            stop_detail_url(trip.pk, stop.pk),
            {"title": "Paragliding week", "budget": "9000.00"},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Stop updated."
        stop.refresh_from_db()
        assert stop.title == "Paragliding week"

    def test_patch_cannot_move_a_stop_outside_the_trip(self, client, trip, stop):
        response = client.patch(
            stop_detail_url(trip.pk, stop.pk),
            {"end_date": str(trip.end_date + timedelta(days=3))},
            format="json",
        )

        assert response.status_code == 400

    def test_order_cannot_be_patched(self, client, trip, stop):
        """Reordering goes through the reorder endpoint, which does it atomically."""
        client.patch(stop_detail_url(trip.pk, stop.pk), {"order": 42}, format="json")

        stop.refresh_from_db()
        assert stop.order != 42

    def test_delete_soft_deletes_the_stop_and_its_activities(self, client, trip, stop):
        activity = TripActivityFactory(trip_stop=stop, day_date=trip.start_date)

        response = client.delete(stop_detail_url(trip.pk, stop.pk))

        assert response.status_code == 204
        assert not TripStop.objects.filter(pk=stop.pk).exists()
        assert not TripActivity.objects.filter(pk=activity.pk).exists()

    def test_a_stop_on_somebody_elses_trip_is_a_404(self, client, other_user):
        stranger_trip = TripFactory(user=other_user)
        stranger_stop = TripStopFactory(
            trip=stranger_trip,
            start_date=stranger_trip.start_date,
            end_date=stranger_trip.end_date,
        )

        response = client.get(stop_detail_url(stranger_trip.pk, stranger_stop.pk))

        assert response.status_code == 404


class TestStopReorder:
    def test_it_returns_the_reordered_list(self, client, trip):
        first = TripStopFactory(
            trip=trip,
            order=1,
            start_date=trip.start_date,
            end_date=trip.start_date + timedelta(days=1),
        )
        second = TripStopFactory(
            trip=trip,
            order=2,
            start_date=trip.start_date + timedelta(days=2),
            end_date=trip.start_date + timedelta(days=3),
        )

        response = client.post(
            reverse("trip-stop-reorder", args=[trip.pk]),
            {"items": [{"id": second.pk, "order": 1}, {"id": first.pk, "order": 2}]},
            format="json",
        )
        body = response.json()

        assert response.status_code == 200
        assert body["message"] == "Stops reordered."
        assert [row["id"] for row in body["data"]] == [second.pk, first.pk]

    def test_a_stop_from_another_trip_is_a_400(self, client, trip):
        stranger = TripStopFactory()

        response = client.post(
            reverse("trip-stop-reorder", args=[trip.pk]),
            {"items": [{"id": stranger.pk, "order": 1}]},
            format="json",
        )

        assert response.status_code == 400

    def test_an_empty_batch_is_a_400(self, client, trip):
        response = client.post(
            reverse("trip-stop-reorder", args=[trip.pk]), {"items": []}, format="json"
        )

        assert response.status_code == 400


# ----------------------------------------------------------- trip activities


class TestTripActivityCreate:
    @pytest.fixture
    def stop(self, trip):
        return TripStopFactory(
            trip=trip, start_date=trip.start_date, end_date=trip.start_date + timedelta(days=3)
        )

    def url(self, trip_id, stop_id) -> str:
        return reverse("trip-activity-list", args=[trip_id, stop_id])

    def test_a_catalog_activity_is_snapshotted(self, client, trip, stop):
        activity = ActivityFactory(
            name="Paragliding at Bir Billing",
            cost=Decimal("2500.00"),
            duration_minutes=90,
            activity_type=ActivityType.ADVENTURE,
        )

        response = client.post(
            self.url(trip.pk, stop.pk),
            {"activity": activity.pk, "day_date": str(stop.start_date)},
            format="json",
        )
        body = response.json()

        assert response.status_code == 201
        assert body["message"] == "Activity added."
        assert body["data"]["title"] == "Paragliding at Bir Billing"
        assert body["data"]["activity_id"] == activity.pk
        assert body["data"]["activity_type"] == ActivityType.ADVENTURE
        assert body["data"]["cost"] == "2500.00"
        assert body["data"]["duration_minutes"] == 90
        assert body["data"]["order"] == 1

    def test_a_custom_entry_needs_no_catalog_row(self, client, trip, stop):
        response = client.post(
            self.url(trip.pk, stop.pk),
            {
                "custom_title": "Coffee with Ana",
                "day_date": str(stop.start_date),
                "cost": "300.00",
            },
            format="json",
        )
        body = response.json()

        assert response.status_code == 201
        assert body["data"]["title"] == "Coffee with Ana"
        assert body["data"]["activity_id"] is None
        assert body["data"]["activity_type"] is None

    def test_both_a_catalog_row_and_a_title_is_rejected(self, client, trip, stop):
        response = client.post(
            self.url(trip.pk, stop.pk),
            {
                "activity": ActivityFactory().pk,
                "custom_title": "Both",
                "day_date": str(stop.start_date),
            },
            format="json",
        )

        assert response.status_code == 400
        assert "custom_title" in response.json()["errors"]["fields"]

    def test_neither_a_catalog_row_nor_a_title_is_rejected(self, client, trip, stop):
        response = client.post(
            self.url(trip.pk, stop.pk), {"day_date": str(stop.start_date)}, format="json"
        )

        assert response.status_code == 400
        assert "custom_title" in response.json()["errors"]["fields"]

    def test_a_day_outside_the_stop_is_rejected(self, client, trip, stop):
        response = client.post(
            self.url(trip.pk, stop.pk),
            {"custom_title": "Too late", "day_date": str(stop.end_date + timedelta(days=1))},
            format="json",
        )

        assert response.status_code == 400
        assert "day_date" in response.json()["errors"]["fields"]

    def test_an_end_time_before_the_start_time_is_rejected(self, client, trip, stop):
        response = client.post(
            self.url(trip.pk, stop.pk),
            {
                "custom_title": "Backwards",
                "day_date": str(stop.start_date),
                "start_time": "11:00:00",
                "end_time": "09:30:00",
            },
            format="json",
        )

        assert response.status_code == 400
        assert "end_time" in response.json()["errors"]["fields"]

    def test_currency_follows_the_trip(self, client, trip, stop):
        trip.currency = "EUR"
        trip.save(update_fields=["currency"])

        response = client.post(
            self.url(trip.pk, stop.pk),
            {"activity": ActivityFactory(currency="USD").pk, "day_date": str(stop.start_date)},
            format="json",
        )

        assert response.json()["data"]["currency"] == "EUR"

    def test_cannot_add_to_a_stop_on_somebody_elses_trip(self, client, other_user):
        stranger_trip = TripFactory(user=other_user)
        stranger_stop = TripStopFactory(
            trip=stranger_trip,
            start_date=stranger_trip.start_date,
            end_date=stranger_trip.end_date,
        )

        response = client.post(
            self.url(stranger_trip.pk, stranger_stop.pk),
            {"custom_title": "Nope", "day_date": str(stranger_trip.start_date)},
            format="json",
        )

        assert response.status_code == 404
        assert not TripActivity.objects.exists()

    def test_list_returns_the_stops_activities_in_day_order(self, client, trip, stop):
        later = TripActivityFactory(
            trip_stop=stop, day_date=stop.start_date + timedelta(days=1), order=1
        )
        earlier = TripActivityFactory(trip_stop=stop, day_date=stop.start_date, order=1)

        body = client.get(self.url(trip.pk, stop.pk)).json()

        assert [row["id"] for row in body["data"]["results"]] == [earlier.pk, later.pk]


class TestTripActivityDetail:
    @pytest.fixture
    def stop(self, trip):
        return TripStopFactory(
            trip=trip, start_date=trip.start_date, end_date=trip.start_date + timedelta(days=3)
        )

    @pytest.fixture
    def trip_activity(self, stop):
        return TripActivityFactory(trip_stop=stop, day_date=stop.start_date)

    def url(self, activity_id) -> str:
        return reverse("trip-activity-detail", args=[activity_id])

    def test_patch_updates_time_and_cost(self, client, trip_activity):
        response = client.patch(
            self.url(trip_activity.pk),
            {"start_time": "09:30:00", "end_time": "11:00:00", "cost": "1750.00"},
            format="json",
        )
        body = response.json()

        assert response.status_code == 200
        assert body["message"] == "Activity updated."
        assert body["data"]["start_time"] == "09:30:00"
        assert body["data"]["cost"] == "1750.00"

    def test_patch_cannot_move_the_day_outside_the_stop(self, client, stop, trip_activity):
        response = client.patch(
            self.url(trip_activity.pk),
            {"day_date": str(stop.end_date + timedelta(days=2))},
            format="json",
        )

        assert response.status_code == 400
        assert "day_date" in response.json()["errors"]["fields"]

    def test_the_catalog_link_cannot_be_swapped_by_patch(self, client, trip_activity):
        """`activity` is not a writable field — it would break the xor constraint."""
        other = ActivityFactory()

        client.patch(self.url(trip_activity.pk), {"activity": other.pk}, format="json")

        trip_activity.refresh_from_db()
        assert trip_activity.activity_id is None

    def test_delete_soft_deletes_the_activity(self, client, trip_activity):
        response = client.delete(self.url(trip_activity.pk))

        assert response.status_code == 204
        assert not TripActivity.objects.filter(pk=trip_activity.pk).exists()
        assert TripActivity.all_objects.filter(pk=trip_activity.pk).exists()

    def test_somebody_elses_activity_is_a_404(self, client, other_user):
        stranger_trip = TripFactory(user=other_user)
        stranger_stop = TripStopFactory(
            trip=stranger_trip,
            start_date=stranger_trip.start_date,
            end_date=stranger_trip.end_date,
        )
        stranger_activity = TripActivityFactory(
            trip_stop=stranger_stop, day_date=stranger_trip.start_date
        )

        assert client.get(self.url(stranger_activity.pk)).status_code == 404
        assert client.delete(self.url(stranger_activity.pk)).status_code == 404
        assert TripActivity.objects.filter(pk=stranger_activity.pk).exists()


class TestTripActivityReorder:
    def test_it_moves_an_activity_to_another_stop_and_day(self, client, trip):
        early = TripStopFactory(
            trip=trip,
            order=1,
            start_date=trip.start_date,
            end_date=trip.start_date + timedelta(days=2),
        )
        late = TripStopFactory(
            trip=trip,
            order=2,
            start_date=trip.start_date + timedelta(days=3),
            end_date=trip.start_date + timedelta(days=5),
        )
        activity = TripActivityFactory(trip_stop=early, day_date=early.start_date, order=1)

        response = client.post(
            reverse("trip-activity-reorder", args=[trip.pk]),
            {
                "items": [
                    {
                        "id": activity.pk,
                        "order": 1,
                        "trip_stop": late.pk,
                        "day_date": str(late.start_date),
                    }
                ]
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Activities reordered."
        activity.refresh_from_db()
        assert activity.trip_stop_id == late.pk
        assert activity.day_date == late.start_date

    def test_a_landing_day_outside_the_target_stop_is_a_400(self, client, trip):
        early = TripStopFactory(
            trip=trip,
            order=1,
            start_date=trip.start_date,
            end_date=trip.start_date + timedelta(days=2),
        )
        late = TripStopFactory(
            trip=trip,
            order=2,
            start_date=trip.start_date + timedelta(days=3),
            end_date=trip.start_date + timedelta(days=5),
        )
        activity = TripActivityFactory(trip_stop=early, day_date=early.start_date, order=1)

        response = client.post(
            reverse("trip-activity-reorder", args=[trip.pk]),
            {"items": [{"id": activity.pk, "order": 1, "trip_stop": late.pk}]},
            format="json",
        )

        assert response.status_code == 400
        activity.refresh_from_db()
        assert activity.trip_stop_id == early.pk


# ------------------------------------------- the trip payloads, now with stops


class TestTripPayloadsWithStops:
    def test_list_row_carries_the_stop_aggregates(self, client, trip):
        bir = TripStopFactory(
            trip=trip,
            order=1,
            city=CityFactory(name="Bir"),
            start_date=trip.start_date,
            end_date=trip.start_date + timedelta(days=2),
        )
        TripStopFactory(
            trip=trip,
            order=2,
            city=CityFactory(name="Manali"),
            start_date=trip.start_date + timedelta(days=3),
            end_date=trip.start_date + timedelta(days=5),
        )
        TripActivityFactory.create_batch(3, trip_stop=bir, day_date=trip.start_date)

        row = client.get(LIST_URL).json()["data"]["results"][0]

        assert row["stops_count"] == 2
        assert row["cities"] == ["Bir", "Manali"]
        assert row["activities_count"] == 3

    def test_a_deleted_stops_activities_stop_counting(self, client, trip):
        stop = TripStopFactory(
            trip=trip, start_date=trip.start_date, end_date=trip.start_date + timedelta(days=2)
        )
        TripActivityFactory.create_batch(2, trip_stop=stop, day_date=trip.start_date)
        stop.delete()

        row = client.get(LIST_URL).json()["data"]["results"][0]

        assert row["stops_count"] == 0
        assert row["activities_count"] == 0

    def test_detail_nests_stops_with_their_activities(self, client, trip):
        stop = TripStopFactory(
            trip=trip,
            city=CityFactory(name="Bir"),
            start_date=trip.start_date,
            end_date=trip.start_date + timedelta(days=2),
        )
        activity = TripActivityFactory(
            trip_stop=stop, custom_title="Paragliding", day_date=trip.start_date
        )

        body = client.get(detail_url(trip.pk)).json()

        assert len(body["data"]["stops"]) == 1
        nested = body["data"]["stops"][0]
        assert nested["city"]["name"] == "Bir"
        assert [item["id"] for item in nested["activities"]] == [activity.pk]
        assert nested["activities"][0]["title"] == "Paragliding"

    def test_detail_query_count_does_not_grow_with_the_itinerary(
        self, client, trip, django_assert_num_queries
    ):
        """Trap #9 again: the deep prefetch must stay a fixed number of queries."""
        stop = TripStopFactory(
            trip=trip, start_date=trip.start_date, end_date=trip.start_date + timedelta(days=2)
        )
        TripActivityFactory(trip_stop=stop, day_date=trip.start_date)

        with django_assert_num_queries(4) as captured:
            client.get(detail_url(trip.pk))

        for index in range(3):
            extra = TripStopFactory(
                trip=trip,
                start_date=trip.start_date + timedelta(days=3 + index),
                end_date=trip.start_date + timedelta(days=3 + index),
            )
            TripActivityFactory.create_batch(2, trip_stop=extra, day_date=extra.start_date)

        with django_assert_num_queries(len(captured.captured_queries)):
            client.get(detail_url(trip.pk))

    def test_filtering_by_city_finds_trips_containing_it(self, client, user, trip):
        bir = CityFactory(name="Bir")
        TripStopFactory(
            trip=trip,
            city=bir,
            start_date=trip.start_date,
            end_date=trip.start_date + timedelta(days=2),
        )
        other = TripFactory(user=user)
        TripStopFactory(
            trip=other,
            city=CityFactory(name="Goa"),
            start_date=other.start_date,
            end_date=other.end_date,
        )

        body = client.get(LIST_URL, {"city": bir.pk}).json()

        assert [row["id"] for row in body["data"]["results"]] == [trip.pk]

    def test_filtering_by_country_finds_trips_containing_it(self, client, trip):
        city = CityFactory()
        TripStopFactory(
            trip=trip,
            city=city,
            start_date=trip.start_date,
            end_date=trip.start_date + timedelta(days=2),
        )

        body = client.get(LIST_URL, {"country": city.country_id}).json()

        assert [row["id"] for row in body["data"]["results"]] == [trip.pk]

    def test_a_trip_is_not_listed_twice_when_two_stops_match(self, client, trip):
        city = CityFactory()
        TripStopFactory(
            trip=trip,
            city=city,
            start_date=trip.start_date,
            end_date=trip.start_date + timedelta(days=1),
        )
        TripStopFactory(
            trip=trip,
            city=city,
            start_date=trip.start_date + timedelta(days=2),
            end_date=trip.start_date + timedelta(days=3),
        )

        body = client.get(LIST_URL, {"city": city.pk}).json()

        assert body["data"]["pagination"]["count"] == 1
