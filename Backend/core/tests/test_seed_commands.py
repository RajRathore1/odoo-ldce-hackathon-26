"""
The seed pipeline, end to end (task B3.5).

A project-level test rather than an app one: `seed_all` spans `geo`,
`activities`, `trips` and `budget`, and what it is really asserting is "a fresh
database is demo-ready". Every test here starts from an empty database, which is
exactly the `rm db.sqlite3 && migrate && seed_all` path in the README.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db.models import Count, Q

from apps.activities.models import Activity, ActivityCategory
from apps.geo.models import City, Country
from apps.trips.constants import TripStatus
from apps.trips.models import Trip, TripActivity, TripStop

pytestmark = pytest.mark.django_db

MIN_ACTIVITIES_PER_CITY = 3


@pytest.fixture
def seeded():
    """A freshly seeded database. Slow, so the assertions below share one."""
    call_command("seed_all", verbosity=0)


class TestSeedGeo:
    def test_it_loads_the_catalog(self):
        call_command("seed_geo", verbosity=0)

        assert Country.objects.count() >= 20
        assert City.objects.count() >= 50

    def test_city_text_survives_the_round_trip(self):
        """
        The mojibake check. `Île-de-France` only stays intact if the fixture is
        opened as UTF-8 — read it with the Windows ANSI codepage and it lands as
        `ÃŽle-de-France`, which is what `loaddata` does without `PYTHONUTF8=1`.
        """
        call_command("seed_geo", verbosity=0)

        paris = City.objects.get(name="Paris")
        assert paris.state == "Île-de-France"
        assert paris.country.flag_emoji == "🇫🇷"

    def test_every_city_has_coordinates_and_a_picture(self):
        call_command("seed_geo", verbosity=0)

        assert not City.objects.filter(latitude__isnull=True).exists()
        assert not City.objects.filter(image_url="").exists()

    def test_it_is_idempotent(self):
        call_command("seed_geo", verbosity=0)
        counts = (Country.objects.count(), City.objects.count())

        call_command("seed_geo", verbosity=0)

        assert (Country.objects.count(), City.objects.count()) == counts

    def test_it_does_not_collide_with_the_dev_fixture(self):
        """
        `dev_seed.json` holds a few of the same countries under the same names.
        Both `Country.iso2` and `Country.name` are unique, so a naive
        `update_or_create` on one of them raises IntegrityError on the other.
        """
        call_command("loaddata", "dev_seed", verbosity=0)

        call_command("seed_geo", verbosity=0)  # must not raise

        assert Country.objects.filter(name="India").count() == 1

    def test_it_leaves_an_earned_popularity_score_alone(self):
        call_command("seed_geo", verbosity=0)
        city = City.objects.first()
        City.objects.filter(pk=city.pk).update(popularity_score=42)

        call_command("seed_geo", verbosity=0)

        city.refresh_from_db()
        assert city.popularity_score == 42


class TestSeedActivities:
    def test_every_city_has_something_to_show(self):
        """
        Screen 8 gets searched in front of judges. A city with no activities
        reads as a broken API, so this is the guarantee the baseline exists for.
        """
        call_command("seed_geo", verbosity=0)
        call_command("seed_activities", verbosity=0)

        thin = (
            City.objects.annotate(
                total=Count("activities", filter=Q(activities__is_deleted=False))
            )
            .filter(total__lt=MIN_ACTIVITIES_PER_CITY)
            .values_list("name", flat=True)
        )

        assert list(thin) == []

    def test_it_loads_a_full_catalog(self):
        call_command("seed_geo", verbosity=0)
        call_command("seed_activities", verbosity=0)

        assert ActivityCategory.objects.count() >= 8
        assert Activity.objects.count() >= 300

    def test_the_curated_activities_are_there(self):
        call_command("seed_geo", verbosity=0)
        call_command("seed_activities", verbosity=0)

        paragliding = Activity.objects.get(name="Tandem paragliding at Bir Billing")
        assert paragliding.city.name == "Bir"
        assert paragliding.activity_type == "ADVENTURE"
        assert paragliding.cost > 0

    def test_an_activity_inherits_its_citys_currency(self):
        """One trip, one currency — a JPY activity in an INR trip breaks the budget."""
        call_command("seed_geo", verbosity=0)
        call_command("seed_activities", verbosity=0)

        for city_name, currency in (("Tokyo", "JPY"), ("Bir", "INR"), ("Paris", "EUR")):
            costs = Activity.objects.filter(city__name=city_name).values_list(
                "currency", flat=True
            )
            assert set(costs) == {currency}, city_name

    def test_ratings_are_stable_across_runs(self):
        """A re-seed must not reshuffle the catalog — hence no `random`."""
        call_command("seed_geo", verbosity=0)
        call_command("seed_activities", verbosity=0)
        before = dict(Activity.objects.values_list("pk", "rating"))

        call_command("seed_activities", verbosity=0)

        assert dict(Activity.objects.values_list("pk", "rating")) == before

    def test_two_cities_sharing_a_name_both_get_a_baseline(self):
        """
        `Paris` exists in more than one country. Keying the baseline loop by
        city *name* silently skipped one of them, which is how a search screen
        ends up with an empty city.
        """
        call_command("seed_geo", verbosity=0)
        france_paris = City.objects.get(name="Paris")
        texas = Country.objects.get(iso2="US")
        other_paris = City.objects.create(country=texas, name="Paris", state="Texas")

        call_command("seed_activities", verbosity=0)

        for city in (france_paris, other_paris):
            assert (
                Activity.objects.filter(city=city).count() >= MIN_ACTIVITIES_PER_CITY
            ), city.state

    def test_it_refuses_to_run_before_seed_geo(self):
        from django.core.management.base import CommandError

        with pytest.raises(CommandError):
            call_command("seed_activities", verbosity=0)


class TestSeedDemo:
    def test_the_documented_credentials_work(self, seeded):
        user = get_user_model().objects.get(email="demo@globetrotter.dev")

        assert user.check_password("Demo@1234")
        assert user.is_active

    def test_all_three_screen_six_tabs_have_a_trip(self, seeded):
        """Two empty tabs read as a bug in front of judges."""
        user = get_user_model().objects.get(email="demo@globetrotter.dev")
        statuses = set(Trip.objects.filter(user=user).values_list("status", flat=True))

        assert statuses == {
            TripStatus.ONGOING,
            TripStatus.PLANNED,
            TripStatus.COMPLETED,
        }

    def test_every_trip_has_stops_activities_and_expenses(self, seeded):
        user = get_user_model().objects.get(email="demo@globetrotter.dev")

        for trip in Trip.objects.filter(user=user):
            assert TripStop.objects.filter(trip=trip).count() >= 2, trip.name
            assert TripActivity.objects.filter(trip_stop__trip=trip).exists(), trip.name
            assert trip.expenses.exists(), trip.name

    def test_the_budget_numbers_add_up(self, seeded):
        from apps.budget.services import trip_cost_summary

        user = get_user_model().objects.get(email="demo@globetrotter.dev")
        trip = Trip.objects.filter(user=user).first()

        summary = trip_cost_summary(trip)

        assert summary["activities_cost"] > 0
        assert summary["expenses_cost"] > 0
        assert summary["grand_total"] == summary["activities_cost"] + summary["expenses_cost"]
        assert summary["remaining"] is not None

    def test_every_stop_is_inside_its_trip(self, seeded):
        """The itinerary only emits dates in range, so a stray stop would vanish."""
        for stop in TripStop.objects.select_related("trip"):
            assert stop.trip.start_date <= stop.start_date
            assert stop.end_date <= stop.trip.end_date

    def test_every_activity_is_inside_its_stop(self, seeded):
        for activity in TripActivity.objects.select_related("trip_stop"):
            stop = activity.trip_stop
            assert stop.start_date <= activity.day_date <= stop.end_date

    def test_re_running_does_not_double_the_trips(self, seeded):
        user = get_user_model().objects.get(email="demo@globetrotter.dev")
        assert Trip.objects.filter(user=user).count() == 3

        call_command("seed_demo", verbosity=0)

        assert Trip.objects.filter(user=user).count() == 3
        # Hard delete, so no soft-deleted leftovers inflating admin analytics.
        assert Trip.all_objects.filter(user=user).count() == 3


class TestSeedAll:
    def test_popularity_reflects_the_seeded_trips(self, seeded):
        """
        `seed_all` finishes with `recalc_popularity`, so the "popular cities"
        list is honest instead of depending on the order things were created in.
        """
        assert City.objects.filter(popularity_score__gt=0).exists()

        for city in City.objects.filter(popularity_score__gt=0):
            assert city.popularity_score == TripStop.objects.filter(city=city).count()

    def test_skip_demo_leaves_the_catalog_only(self):
        call_command("seed_all", "--skip-demo", verbosity=0)

        assert City.objects.exists()
        assert Activity.objects.exists()
        assert not Trip.objects.exists()

    def test_running_it_twice_is_safe(self, seeded):
        cities = City.objects.count()
        activities = Activity.objects.count()

        call_command("seed_all", verbosity=0)

        assert City.objects.count() == cities
        assert Activity.objects.count() == activities
        assert Trip.objects.count() == 3
