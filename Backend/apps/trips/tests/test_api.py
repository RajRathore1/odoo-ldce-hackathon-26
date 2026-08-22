"""trips — status codes, envelope shape, permissions."""

import io
from datetime import date, timedelta

import pytest
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, UserFactory
from apps.trips.constants import TripStatus
from apps.trips.models import Trip
from apps.trips.tests.factories import TripFactory

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
        """Trap #9. The list must be flat, whatever the page size."""
        TripFactory.create_batch(3, user=user)
        with django_assert_num_queries(3) as captured:
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
