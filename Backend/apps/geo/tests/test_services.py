"""geo — service behaviour: bookmarks and the popularity rebuild."""

import pytest

from apps.geo.models import City, SavedDestination
from apps.geo.services import (
    recalculate_city_popularity,
    remove_saved_destination,
    save_destination,
)
from apps.geo.tests.factories import CityFactory
from apps.trips.tests.factories import TripStopFactory
from core.exceptions import ConflictError

pytestmark = pytest.mark.django_db


class TestSaveDestination:
    def test_it_bookmarks_a_city(self, django_user_model):
        user = django_user_model.objects.create_user(
            email="riya@example.com", password="x", first_name="Riya"
        )
        city = CityFactory()

        saved = save_destination(user=user, city=city, note="paragliding")

        assert saved.note == "paragliding"
        assert SavedDestination.objects.filter(user=user, city=city).exists()

    def test_a_duplicate_is_a_conflict_not_a_silent_no_op(self, django_user_model):
        """The frontend draws the bookmark from `is_saved`; a stale client should hear about it."""
        user = django_user_model.objects.create_user(
            email="riya@example.com", password="x", first_name="Riya"
        )
        city = CityFactory()
        save_destination(user=user, city=city)

        with pytest.raises(ConflictError):
            save_destination(user=user, city=city)

    def test_removing_then_re_saving_works(self, django_user_model):
        user = django_user_model.objects.create_user(
            email="riya@example.com", password="x", first_name="Riya"
        )
        city = CityFactory()
        remove_saved_destination(save_destination(user=user, city=city))

        assert save_destination(user=user, city=city)


class TestRecalculateCityPopularity:
    def test_it_counts_the_trip_stops_pointing_at_each_city(self):
        busy, quiet = CityFactory(), CityFactory()
        TripStopFactory.create_batch(3, city=busy)
        TripStopFactory(city=quiet)

        recalculate_city_popularity()

        busy.refresh_from_db()
        quiet.refresh_from_db()
        assert (busy.popularity_score, quiet.popularity_score) == (3, 1)

    def test_it_corrects_a_drifted_counter(self):
        """This is the repair job — the number it finds is the number it writes."""
        city = CityFactory()
        City.objects.filter(pk=city.pk).update(popularity_score=999)
        TripStopFactory(city=city)

        recalculate_city_popularity()

        city.refresh_from_db()
        assert city.popularity_score == 1

    def test_a_city_with_no_stops_goes_to_zero(self):
        city = CityFactory()
        City.objects.filter(pk=city.pk).update(popularity_score=42)

        recalculate_city_popularity()

        city.refresh_from_db()
        assert city.popularity_score == 0

    def test_a_deleted_stop_does_not_count(self):
        """Trap #2 — soft delete does not cascade, so the filter has to be explicit."""
        city = CityFactory()
        TripStopFactory(city=city)
        TripStopFactory(city=city).delete()

        recalculate_city_popularity()

        city.refresh_from_db()
        assert city.popularity_score == 1

    def test_it_can_be_scoped_to_one_city(self):
        target, untouched = CityFactory(), CityFactory()
        City.objects.filter(pk=untouched.pk).update(popularity_score=999)
        TripStopFactory(city=target)

        recalculate_city_popularity(target.pk)

        target.refresh_from_db()
        untouched.refresh_from_db()
        assert target.popularity_score == 1
        assert untouched.popularity_score == 999

    def test_it_is_a_single_statement(self, django_assert_num_queries):
        """One correlated UPDATE, not one query per city."""
        CityFactory.create_batch(5)

        with django_assert_num_queries(1):
            recalculate_city_popularity()
