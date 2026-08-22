"""trips — model behaviour: constraints, properties, the status sync."""

from datetime import date, timedelta

import pytest
from django.db.utils import IntegrityError

from apps.trips.constants import TripStatus
from apps.trips.models import Trip
from apps.trips.tests.factories import TripFactory

pytestmark = pytest.mark.django_db

TODAY = date.today()


class TestStatusFromDates:
    """Pure function — no DB, so the boundaries are worth nailing down."""

    def test_future_trip_is_planned(self):
        assert (
            Trip.status_from_dates(TODAY + timedelta(days=1), TODAY + timedelta(days=5))
            == TripStatus.PLANNED
        )

    def test_past_trip_is_completed(self):
        assert (
            Trip.status_from_dates(TODAY - timedelta(days=9), TODAY - timedelta(days=2))
            == TripStatus.COMPLETED
        )

    def test_trip_spanning_today_is_ongoing(self):
        assert (
            Trip.status_from_dates(TODAY - timedelta(days=1), TODAY + timedelta(days=1))
            == TripStatus.ONGOING
        )

    def test_starting_today_is_ongoing_not_planned(self):
        """The inclusive boundary: day one of a trip is already ongoing."""
        assert Trip.status_from_dates(TODAY, TODAY + timedelta(days=3)) == TripStatus.ONGOING

    def test_ending_today_is_ongoing_not_completed(self):
        """The other inclusive boundary: it is not over until the day is."""
        assert Trip.status_from_dates(TODAY - timedelta(days=3), TODAY) == TripStatus.ONGOING

    def test_single_day_trip_today_is_ongoing(self):
        assert Trip.status_from_dates(TODAY, TODAY) == TripStatus.ONGOING


class TestStatusSyncOnSave:
    def test_save_derives_status_from_dates(self):
        trip = TripFactory(
            start_date=TODAY - timedelta(days=5), end_date=TODAY - timedelta(days=1)
        )
        assert trip.status == TripStatus.COMPLETED

    def test_moving_the_dates_moves_the_status(self):
        trip = TripFactory(
            start_date=TODAY + timedelta(days=10), end_date=TODAY + timedelta(days=20)
        )
        assert trip.status == TripStatus.PLANNED

        trip.start_date = TODAY - timedelta(days=1)
        trip.end_date = TODAY + timedelta(days=1)
        trip.save()

        trip.refresh_from_db()
        assert trip.status == TripStatus.ONGOING

    def test_draft_is_never_overwritten(self):
        """Trap #4: a draft whose dates are in the past is still a draft."""
        trip = TripFactory(
            status=TripStatus.DRAFT,
            start_date=TODAY - timedelta(days=5),
            end_date=TODAY - timedelta(days=1),
        )
        assert trip.status == TripStatus.DRAFT

        trip.save()
        trip.refresh_from_db()
        assert trip.status == TripStatus.DRAFT

    def test_cancelled_is_never_overwritten(self):
        trip = TripFactory(status=TripStatus.CANCELLED, start_date=TODAY, end_date=TODAY)
        trip.save()
        trip.refresh_from_db()
        assert trip.status == TripStatus.CANCELLED

    def test_partial_save_still_persists_the_synced_status(self):
        """
        A save with `update_fields` must not leave the row's status disagreeing
        with the object it was written from.
        """
        trip = TripFactory(
            start_date=TODAY + timedelta(days=5), end_date=TODAY + timedelta(days=9)
        )
        Trip.objects.filter(pk=trip.pk).update(
            start_date=TODAY, end_date=TODAY + timedelta(days=2)
        )

        trip.refresh_from_db()
        trip.views_count = 7
        trip.save(update_fields=["views_count"])

        trip.refresh_from_db()
        assert trip.views_count == 7
        assert trip.status == TripStatus.ONGOING


class TestConstraints:
    def test_end_date_before_start_date_is_rejected_by_the_database(self):
        with pytest.raises(IntegrityError):
            TripFactory(start_date=TODAY + timedelta(days=5), end_date=TODAY)

    def test_share_token_is_unique_per_trip(self):
        first, second = TripFactory(), TripFactory()
        assert first.share_token != second.share_token


class TestProperties:
    def test_duration_counts_both_ends(self):
        trip = TripFactory(start_date=date(2026, 6, 1), end_date=date(2026, 6, 3))
        assert trip.duration_days == 3

    def test_single_day_trip_is_one_day(self):
        trip = TripFactory(start_date=date(2026, 6, 1), end_date=date(2026, 6, 1))
        assert trip.duration_days == 1

    def test_share_url_points_at_the_frontend(self, settings):
        settings.FRONTEND_BASE_URL = "http://localhost:3000"
        trip = TripFactory()
        assert trip.share_url == f"http://localhost:3000/trips/shared/{trip.share_token}"


class TestSoftDelete:
    def test_delete_hides_the_trip_but_keeps_the_row(self):
        trip = TripFactory()
        trip.delete()

        assert not Trip.objects.filter(pk=trip.pk).exists()
        assert Trip.all_objects.filter(pk=trip.pk).exists()
        assert Trip.all_objects.get(pk=trip.pk).is_deleted is True
