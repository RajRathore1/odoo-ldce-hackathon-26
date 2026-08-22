"""activities — `factory_boy` factories for this app's models."""

from decimal import Decimal

import factory

from apps.activities.constants import ActivityType
from apps.activities.models import Activity, ActivityCategory
from apps.geo.tests.factories import CityFactory


class ActivityCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ActivityCategory

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")


class ActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Activity

    city = factory.SubFactory(CityFactory)
    category = factory.SubFactory(ActivityCategoryFactory)
    name = factory.Sequence(lambda n: f"Activity {n}")
    activity_type = ActivityType.SIGHTSEEING
    # `Decimal`, not a string: a factory-built object is used unrefreshed, and a
    # string here would make `activity.cost` a `str` in memory but a `Decimal`
    # once reloaded.
    cost = Decimal("1500.00")
    currency = "INR"
    duration_minutes = 90
