"""geo — `factory_boy` factories for this app's models."""

import factory

from apps.geo.models import City, Country


class CountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Country

    name = factory.Sequence(lambda n: f"Country {n}")
    # `iso2` is unique and two characters, so it cannot come from a plain
    # sequence past 99 — the alphabet pair keeps it collision-free for the
    # handful of countries any one test needs.
    iso2 = factory.Sequence(lambda n: f"{chr(65 + n // 26)}{chr(65 + n % 26)}")
    region = "Asia"
    currency_code = "INR"


class CityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = City

    country = factory.SubFactory(CountryFactory)
    name = factory.Sequence(lambda n: f"City {n}")
    state = ""
    currency = "INR"
