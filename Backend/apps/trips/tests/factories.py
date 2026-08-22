"""trips — `factory_boy` factories for this app's models."""

from datetime import date, timedelta
from decimal import Decimal

import factory

from apps.accounts.tests.factories import UserFactory
from apps.geo.tests.factories import CityFactory
from apps.trips.constants import TripStatus
from apps.trips.models import Trip, TripActivity, TripStop

#: Fixed reference point. Tests that care about `status` pass explicit dates
#: relative to `date.today()`; everything else just wants a valid range.
TODAY = date.today()


class TripFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Trip

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Trip {n}")
    description = ""
    # Default to a future trip, which `Trip.save()` resolves to PLANNED.
    start_date = TODAY + timedelta(days=30)
    end_date = TODAY + timedelta(days=37)
    currency = "INR"


class DraftTripFactory(TripFactory):
    """A draft stays a draft whatever its dates say — trap #4."""

    status = TripStatus.DRAFT


class TripStopFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TripStop

    trip = factory.SubFactory(TripFactory)
    city = factory.SubFactory(CityFactory)
    # Inside `TripFactory`'s default range. Override both when the trip is not
    # the default one, or the stop lands outside its parent.
    start_date = TODAY + timedelta(days=30)
    end_date = TODAY + timedelta(days=33)
    order = factory.Sequence(lambda n: n + 1)


class TripActivityFactory(factory.django.DjangoModelFactory):
    """
    A **custom** entry by default — no catalog row, so most tests need neither a
    city catalog nor an activity catalog. Pass `activity=` for the linked case.
    """

    class Meta:
        model = TripActivity

    trip_stop = factory.SubFactory(TripStopFactory)
    custom_title = factory.Sequence(lambda n: f"Custom activity {n}")
    day_date = TODAY + timedelta(days=30)
    cost = Decimal("500.00")
    currency = "INR"
    order = factory.Sequence(lambda n: n + 1)
