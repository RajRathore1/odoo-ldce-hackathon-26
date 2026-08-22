"""Geographic reference data and the activity catalogue.

Country/Region/SubRegion/City are django-cities-light's models, swapped into
this app via ``CITIES_LIGHT_APP_NAME`` so that City can carry the extra
fields the City Search screen needs (cost index, popularity, blurb, image).

All four subclasses must be declared even where nothing is added -- the swap
resolves every FK against this app. ``connect_default_signals`` is what
populates ``slug``, ``display_name`` and ``search_names`` on save, and the
``cities_light`` import command depends on it.
"""

from cities_light.abstract_models import (
    AbstractCity,
    AbstractCountry,
    AbstractRegion,
    AbstractSubRegion,
)
from cities_light.receivers import connect_default_signals
from django.db import models
from django.utils.text import slugify


class Country(AbstractCountry):
    pass


connect_default_signals(Country)


class Region(AbstractRegion):
    pass


connect_default_signals(Region)


class SubRegion(AbstractSubRegion):
    pass


connect_default_signals(SubRegion)


class City(AbstractCity):
    """cities-light City plus the fields the travel UI needs."""

    cost_index = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text=(
            "Daily-budget tier from 1.0 (cheap) to 5.0 (expensive). "
            "Null for cities outside the curated set."
        ),
    )
    popularity = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Trip stops referencing this city; set by refresh_popularity.",
    )
    blurb = models.TextField(blank=True)
    image = models.ImageField(upload_to="cities/", blank=True)


connect_default_signals(City)


class Activity(models.Model):
    """Something to do in a city -- the catalogue behind Activity Search."""

    class Category(models.TextChoices):
        SIGHTSEEING = "sightseeing", "Sightseeing"
        FOOD = "food", "Food & drink"
        ADVENTURE = "adventure", "Adventure"
        CULTURE = "culture", "Culture"
        NIGHTLIFE = "nightlife", "Nightlife"
        SHOPPING = "shopping", "Shopping"
        NATURE = "nature", "Nature"
        WELLNESS = "wellness", "Wellness"

    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="activities")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    category = models.CharField(
        max_length=20, choices=Category.choices, db_index=True
    )
    description = models.TextField(blank=True)
    cost = models.DecimalField(
        max_digits=9, decimal_places=2, default=0, help_text="Cost per person."
    )
    duration_minutes = models.PositiveIntegerField(default=60)
    image = models.ImageField(upload_to="activities/", blank=True)
    popularity = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Times added to an itinerary; set by refresh_popularity.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "activities"
        constraints = [
            models.UniqueConstraint(
                fields=["city", "slug"], name="uniq_activity_city_slug"
            )
        ]
        # Activity Search filters on city and category together.
        indexes = [models.Index(fields=["city", "category"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:220]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.city.name})"
