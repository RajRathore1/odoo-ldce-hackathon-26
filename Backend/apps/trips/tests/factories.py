"""trips — `factory_boy` factories for this app's models."""

from datetime import date, timedelta

import factory

from apps.accounts.tests.factories import UserFactory
from apps.trips.constants import TripStatus
from apps.trips.models import Trip

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
