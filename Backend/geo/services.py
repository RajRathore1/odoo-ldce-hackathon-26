"""Shared geo lookups used by the seed commands."""

from cities_light.abstract_models import to_ascii
from django.db.models import F, Q

from .models import City


def _by_population(queryset):
    """Largest city first; rows with no population figure last."""
    return queryset.order_by(F("population").desc(nulls_last=True)).first()


def _alternate_name_token(name):
    """Match `name` as a whole entry in the comma-separated alternate_names.

    A bare ``icontains`` would let "York" match "New York", so each of the
    four positions a token can occupy is spelled out instead.
    """
    return (
        Q(alternate_names__iexact=name)
        | Q(alternate_names__istartswith=f"{name},")
        | Q(alternate_names__iendswith=f",{name}")
        | Q(alternate_names__icontains=f",{name},")
    )


def resolve_city(name, country_code):
    """Find a City from a human-written name plus an ISO 3166-1 alpha-2 code.

    Tried in order, first hit wins:

    1. ``name_ascii`` -- GeoNames' own asciiname column. Note this is *not* a
       transliteration of ``name``: GeoNames stores Zurich as "Zuerich", so
       this alone misses a fair few well-known spellings.
    2. ``name`` -- the localised name, for accented fixture entries.
    3. ``alternate_names`` -- catches the English exonyms ("Zurich" for
       Zuerich, "Seville" for Sevilla) that the first two miss.

    The country code is what disambiguates; plenty of city names repeat across
    countries. Where a name repeats *within* one country the largest by
    population wins, which is the intent for a travel catalogue.

    Returns None when nothing matches. Callers report that rather than
    raising, so one bad fixture row cannot abort a whole seed.
    """
    in_country = City.objects.filter(country__code2__iexact=country_code)

    for condition in (
        Q(name_ascii__iexact=to_ascii(name)),
        Q(name__iexact=name),
        _alternate_name_token(name),
    ):
        match = _by_population(in_country.filter(condition))
        if match is not None:
            return match

    return None
