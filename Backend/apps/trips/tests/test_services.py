"""trips — service behaviour: ordering, snapshots and the two reorders."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError

from apps.activities.tests.factories import ActivityFactory
from apps.geo.models import City
from apps.geo.tests.factories import CityFactory
from apps.trips import services
from apps.trips.models import TripActivity, TripStop
from apps.trips.tests.factories import (
    TripActivityFactory,
    TripFactory,
    TripStopFactory,
)

pytestmark = pytest.mark.django_db

TODAY = date.today()


@pytest.fixture
def trip():
    """A ten-day trip, so a stop and a day always have room inside it."""
    return TripFactory(
        start_date=TODAY + timedelta(days=30), end_date=TODAY + timedelta(days=39)
    )


def stop_fields(trip, offset=0, length=2):
    return {
        "city": CityFactory(),
        "start_date": trip.start_date + timedelta(days=offset),
        "end_date": trip.start_date + timedelta(days=offset + length),
    }


class TestCreateStop:
    def test_order_is_assigned_from_the_end(self, trip):
        first = services.create_stop(trip=trip, **stop_fields(trip, 0))
        second = services.create_stop(trip=trip, **stop_fields(trip, 3))

        assert (first.order, second.order) == (1, 2)

    def test_order_restarts_at_one_for_each_trip(self, trip):
        services.create_stop(trip=trip, **stop_fields(trip, 0))
        other = TripFactory(start_date=trip.start_date, end_date=trip.end_date)

        assert services.create_stop(trip=other, **stop_fields(other, 0)).order == 1

    def test_a_soft_deleted_stop_does_not_free_up_its_order(self, trip):
        """`Max(order)` reads live rows only, so a delete-then-add reuses 1."""
        first = services.create_stop(trip=trip, **stop_fields(trip, 0))
        first.delete()

        assert services.create_stop(trip=trip, **stop_fields(trip, 3)).order == 1

    def test_adding_a_stop_bumps_the_city_popularity(self, trip):
        city = CityFactory()
        assert city.popularity_score == 0

        services.create_stop(
            trip=trip,
            city=city,
            start_date=trip.start_date,
            end_date=trip.start_date + timedelta(days=1),
        )

        city.refresh_from_db()
        assert city.popularity_score == 1

    def test_the_bump_is_an_increment_not_a_write_of_a_read_value(self, trip):
        """`F()` expression: two adds must land on 2, never on 1."""
        city = CityFactory()
        City.objects.filter(pk=city.pk).update(popularity_score=41)

        services.create_stop(
            trip=trip,
            city=city,
            start_date=trip.start_date,
            end_date=trip.start_date + timedelta(days=1),
        )

        city.refresh_from_db()
        assert city.popularity_score == 42


class TestDeleteStop:
    def test_deleting_a_stop_soft_deletes_its_activities(self, trip):
        stop = TripStopFactory(
            trip=trip, start_date=trip.start_date, end_date=trip.start_date + timedelta(days=2)
        )
        activity = TripActivityFactory(trip_stop=stop, day_date=trip.start_date)

        services.delete_stop(stop)

        assert not TripStop.objects.filter(pk=stop.pk).exists()
        assert not TripActivity.objects.filter(pk=activity.pk).exists()
        assert TripActivity.all_objects.get(pk=activity.pk).is_deleted is True


class TestCreateTripActivity:
    @pytest.fixture
    def stop(self, trip):
        return TripStopFactory(
            trip=trip, start_date=trip.start_date, end_date=trip.start_date + timedelta(days=3)
        )

    def test_cost_and_duration_are_snapshotted_from_the_catalog(self, stop):
        activity = ActivityFactory(cost=Decimal("2500.00"), duration_minutes=90)

        trip_activity = services.create_trip_activity(
            trip_stop=stop, activity=activity, day_date=stop.start_date, custom_title=""
        )

        assert trip_activity.cost == Decimal("2500.00")
        assert trip_activity.duration_minutes == 90

    def test_editing_the_catalog_afterwards_does_not_move_the_snapshot(self, stop):
        activity = ActivityFactory(cost=Decimal("2500.00"))
        trip_activity = services.create_trip_activity(
            trip_stop=stop, activity=activity, day_date=stop.start_date, custom_title=""
        )

        activity.cost = Decimal("9999.00")
        activity.save(update_fields=["cost"])

        trip_activity.refresh_from_db()
        assert trip_activity.cost == Decimal("2500.00")

    def test_an_explicit_cost_wins_over_the_catalog(self, stop):
        activity = ActivityFactory(cost=Decimal("2500.00"))

        trip_activity = services.create_trip_activity(
            trip_stop=stop,
            activity=activity,
            day_date=stop.start_date,
            custom_title="",
            cost=Decimal("100.00"),
        )

        assert trip_activity.cost == Decimal("100.00")

    def test_currency_comes_from_the_trip_not_the_catalog(self, trip, stop):
        """One trip, one currency — the budget adds children up without converting."""
        trip.currency = "EUR"
        trip.save(update_fields=["currency"])
        activity = ActivityFactory(currency="USD")

        trip_activity = services.create_trip_activity(
            trip_stop=stop, activity=activity, day_date=stop.start_date, custom_title=""
        )

        assert trip_activity.currency == "EUR"

    def test_a_custom_entry_needs_no_catalog_row(self, stop):
        trip_activity = services.create_trip_activity(
            trip_stop=stop, custom_title="Coffee with Ana", day_date=stop.start_date
        )

        assert trip_activity.activity_id is None
        assert trip_activity.title == "Coffee with Ana"

    def test_adding_a_catalog_activity_bumps_its_popularity(self, stop):
        activity = ActivityFactory()

        services.create_trip_activity(
            trip_stop=stop, activity=activity, day_date=stop.start_date, custom_title=""
        )

        activity.refresh_from_db()
        assert activity.popularity_score == 1

    def test_order_is_per_day_not_per_stop(self, stop):
        """Two days each start at 1 — the itinerary renders one list per day."""
        first_day = services.create_trip_activity(
            trip_stop=stop, custom_title="Morning", day_date=stop.start_date
        )
        same_day = services.create_trip_activity(
            trip_stop=stop, custom_title="Afternoon", day_date=stop.start_date
        )
        next_day = services.create_trip_activity(
            trip_stop=stop,
            custom_title="Next morning",
            day_date=stop.start_date + timedelta(days=1),
        )

        assert (first_day.order, same_day.order, next_day.order) == (1, 2, 1)


class TestReorderStops:
    @pytest.fixture
    def stops(self, trip):
        return [
            TripStopFactory(
                trip=trip,
                order=index + 1,
                start_date=trip.start_date + timedelta(days=index * 2),
                end_date=trip.start_date + timedelta(days=index * 2 + 1),
            )
            for index in range(3)
        ]

    def test_it_applies_the_new_order(self, trip, stops):
        first, second, third = stops

        services.reorder_stops(
            trip=trip,
            items=[
                {"id": third.pk, "order": 1},
                {"id": first.pk, "order": 2},
                {"id": second.pk, "order": 3},
            ],
        )

        assert [stop.pk for stop in TripStop.objects.filter(trip=trip)] == [
            third.pk,
            first.pk,
            second.pk,
        ]

    def test_it_is_a_single_statement(self, trip, stops, django_assert_num_queries):
        """
        Trap #2. One `bulk_update`, so `order` is never transiently duplicated —
        which is also why the model carries no unique constraint on it.
        """
        first, second, third = stops
        items = [
            {"id": third.pk, "order": 1},
            {"id": first.pk, "order": 2},
            {"id": second.pk, "order": 3},
        ]

        # One read of the stops, one UPDATE, and the transaction's savepoints.
        with django_assert_num_queries(4):
            services.reorder_stops(trip=trip, items=items)

    def test_a_stop_from_another_trip_is_rejected(self, trip, stops):
        stranger = TripStopFactory()

        with pytest.raises(ValidationError) as caught:
            services.reorder_stops(trip=trip, items=[{"id": stranger.pk, "order": 1}])

        assert "do not belong to this trip" in str(caught.value)

    def test_a_rejected_batch_writes_nothing(self, trip, stops):
        first = stops[0]
        stranger = TripStopFactory()

        with pytest.raises(ValidationError):
            services.reorder_stops(
                trip=trip,
                items=[{"id": first.pk, "order": 9}, {"id": stranger.pk, "order": 1}],
            )

        first.refresh_from_db()
        assert first.order == 1

    def test_it_leaves_updated_at_alone(self, trip, stops):
        """A reorder is not a change to the stop itself."""
        first = stops[0]
        before = first.updated_at

        services.reorder_stops(trip=trip, items=[{"id": first.pk, "order": 3}])

        first.refresh_from_db()
        assert first.updated_at == before


class TestReorderTripActivities:
    @pytest.fixture
    def stops(self, trip):
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
        return early, late

    def test_it_reorders_within_a_day(self, trip, stops):
        early, _ = stops
        first = TripActivityFactory(trip_stop=early, day_date=early.start_date, order=1)
        second = TripActivityFactory(trip_stop=early, day_date=early.start_date, order=2)

        services.reorder_trip_activities(
            trip=trip,
            items=[{"id": second.pk, "order": 1}, {"id": first.pk, "order": 2}],
        )

        first.refresh_from_db()
        second.refresh_from_db()
        assert (second.order, first.order) == (1, 2)

    def test_it_moves_an_activity_to_another_day(self, trip, stops):
        early, _ = stops
        activity = TripActivityFactory(trip_stop=early, day_date=early.start_date, order=1)

        services.reorder_trip_activities(
            trip=trip,
            items=[
                {
                    "id": activity.pk,
                    "order": 1,
                    "day_date": early.start_date + timedelta(days=1),
                }
            ],
        )

        activity.refresh_from_db()
        assert activity.day_date == early.start_date + timedelta(days=1)

    def test_it_moves_an_activity_to_another_stop(self, trip, stops):
        early, late = stops
        activity = TripActivityFactory(trip_stop=early, day_date=early.start_date, order=1)

        services.reorder_trip_activities(
            trip=trip,
            items=[
                {
                    "id": activity.pk,
                    "order": 1,
                    "trip_stop": late.pk,
                    "day_date": late.start_date,
                }
            ],
        )

        activity.refresh_from_db()
        assert activity.trip_stop_id == late.pk
        assert activity.day_date == late.start_date

    def test_a_day_outside_the_target_stop_is_rejected(self, trip, stops):
        early, late = stops
        activity = TripActivityFactory(trip_stop=early, day_date=early.start_date, order=1)

        with pytest.raises(ValidationError) as caught:
            services.reorder_trip_activities(
                trip=trip,
                items=[{"id": activity.pk, "order": 1, "trip_stop": late.pk}],
            )

        assert "outside stop" in str(caught.value)
        activity.refresh_from_db()
        assert activity.trip_stop_id == early.pk

    def test_a_stop_from_another_trip_is_rejected(self, trip, stops):
        early, _ = stops
        activity = TripActivityFactory(trip_stop=early, day_date=early.start_date, order=1)
        stranger = TripStopFactory()

        with pytest.raises(ValidationError) as caught:
            services.reorder_trip_activities(
                trip=trip,
                items=[{"id": activity.pk, "order": 1, "trip_stop": stranger.pk}],
            )

        assert "does not belong to this trip" in str(caught.value)

    def test_an_activity_from_another_trip_is_rejected(self, trip, stops):
        stranger = TripActivityFactory()

        with pytest.raises(ValidationError):
            services.reorder_trip_activities(
                trip=trip, items=[{"id": stranger.pk, "order": 1}]
            )
