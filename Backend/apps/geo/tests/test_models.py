"""geo — constraints, properties and `save()` behaviour."""

import pytest
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.accounts.tests.factories import UserFactory
from apps.activities.models import Activity, ActivityCategory
from apps.geo.models import City, Country, SavedDestination

pytestmark = pytest.mark.django_db


@pytest.fixture
def india():
    return Country.objects.create(name="India", iso2="IN", region="Asia")


@pytest.fixture
def ahmedabad(india):
    return City.objects.create(country=india, name="Ahmedabad", state="Gujarat")


class TestCity:
    def test_display_name_includes_the_state(self, ahmedabad):
        assert ahmedabad.display_name == "Ahmedabad, Gujarat"

    def test_display_name_omits_an_empty_state(self, india):
        city = City.objects.create(country=india, name="Goa", state="")
        assert city.display_name == "Goa"

    def test_same_name_in_the_same_state_is_rejected(self, india, ahmedabad):
        with pytest.raises(IntegrityError), transaction.atomic():
            City.objects.create(country=india, name="Ahmedabad", state="Gujarat")

    def test_same_name_in_a_different_state_is_allowed(self, india, ahmedabad):
        """Hyderabad exists in two Indian states; the constraint must permit it."""
        assert City.objects.create(country=india, name="Ahmedabad", state="Rajasthan")

    def test_country_is_protected_from_deletion(self, india, ahmedabad):
        """
        PROTECT, not CASCADE: deleting a country in the admin must not silently
        take its cities — and the trips referencing them — with it.
        """
        with pytest.raises(ProtectedError):
            india.delete(hard=True)

    def test_ordering_is_by_popularity_then_name(self, india):
        City.objects.create(country=india, name="Zeta", popularity_score=99)
        City.objects.create(country=india, name="Alpha", popularity_score=1)
        assert [c.name for c in City.objects.all()] == ["Zeta", "Alpha"]


class TestSavedDestination:
    def test_a_user_cannot_save_the_same_city_twice(self, ahmedabad):
        user = UserFactory()
        SavedDestination.objects.create(user=user, city=ahmedabad)

        with pytest.raises(IntegrityError), transaction.atomic():
            SavedDestination.objects.create(user=user, city=ahmedabad)

    def test_two_users_can_save_the_same_city(self, ahmedabad):
        SavedDestination.objects.create(user=UserFactory(), city=ahmedabad)
        assert SavedDestination.objects.create(user=UserFactory(), city=ahmedabad)

    def test_a_removed_city_can_be_saved_again(self, ahmedabad):
        """
        The whole point of scoping the unique constraint to `is_deleted=False`.
        Without the condition the soft-deleted row keeps occupying the key and
        the user can never re-save a destination they removed.
        """
        user = UserFactory()
        saved = SavedDestination.objects.create(user=user, city=ahmedabad)
        saved.delete()  # soft

        assert SavedDestination.objects.create(user=user, city=ahmedabad)
        assert SavedDestination.all_objects.filter(user=user, city=ahmedabad).count() == 2


class TestDevSeedFixture:
    """
    Guards `fixtures/dev_seed.json` against model drift.

    The fixture is hand-written, so adding a non-nullable field to `City` or
    `Activity` breaks `loaddata` — and without this test that surfaces only when
    somebody resets their database, which is the worst possible moment.
    """

    def test_it_loads(self):
        call_command("loaddata", "dev_seed", verbosity=0)

        assert Country.objects.count() == 6
        assert City.objects.count() == 10
        assert ActivityCategory.objects.count() == 3
        assert Activity.objects.count() == 20

    def test_timestamps_are_populated(self):
        """
        `loaddata` deserialises with `save_base(raw=True)`, which skips
        `field.pre_save()` — so `auto_now_add` never fires and the fixture has
        to carry `created_at` itself.
        """
        call_command("loaddata", "dev_seed", verbosity=0)
        assert not City.objects.filter(created_at__isnull=True).exists()

    def test_every_seeded_city_has_activities(self):
        """A city with an empty activity list looks like a broken screen."""
        call_command("loaddata", "dev_seed", verbosity=0)
        for city in City.objects.all():
            assert city.activities.exists(), f"{city.name} has no activities"

    def test_it_is_idempotent(self):
        """Explicit pks mean a re-run overwrites rather than duplicating."""
        call_command("loaddata", "dev_seed", verbosity=0)
        call_command("loaddata", "dev_seed", verbosity=0)
        assert City.objects.count() == 10
