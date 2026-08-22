"""
geo — models. Owner: **Dev A** (models) · **Dev B** (endpoints).

`Country`, `City`, `SavedDestination` — see docs/MODELS.md §4.

Dev A owns this file because `TripStop.city` and `User.city` are foreign keys
into it. Every serializer, selector, filter and view on top of these models is
Dev B's — different files.

This app imports **nothing but `core`**. The FK to the user model is the string
`settings.AUTH_USER_MODEL`, which Django resolves lazily, so the one-way import
rule in LAYOUT.md §5 holds.
"""

from django.conf import settings
from django.db import models

from core.models import BaseModel


class Country(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    iso2 = models.CharField(max_length=2, unique=True)
    iso3 = models.CharField(max_length=3, blank=True)
    region = models.CharField(max_length=50, blank=True, db_index=True)
    currency_code = models.CharField(max_length=3, blank=True)
    flag_emoji = models.CharField(max_length=8, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "countries"

    def __str__(self) -> str:
        return self.name


class City(BaseModel):
    country = models.ForeignKey(
        Country,
        # PROTECT: a seeded city must not vanish out from under a live trip
        # because someone tidied up a country row in the admin.
        on_delete=models.PROTECT,
        related_name="cities",
    )
    name = models.CharField(max_length=120, db_index=True)
    state = models.CharField(max_length=120, blank=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    timezone = models.CharField(max_length=50, blank=True)

    # Relative index, 100 = baseline. The spec's "cost index".
    cost_index = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    # Absolute, in `currency`. Surfaced as a budgeting hint on city detail.
    avg_daily_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, blank=True)

    # Denormalised TripStop count. Drives /cities/popular/ and the admin's
    # "Popular Cities" table, both of which would otherwise be a live aggregate
    # over every trip stop on every request.
    popularity_score = models.PositiveIntegerField(default=0, db_index=True)

    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-popularity_score", "name")
        verbose_name_plural = "cities"
        constraints = [
            models.UniqueConstraint(
                fields=["country", "name", "state"], name="uniq_city_country_name_state"
            )
        ]
        indexes = [
            models.Index(fields=["-popularity_score"], name="city_popularity_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name}, {self.country.name}"

    @property
    def display_name(self) -> str:
        """`"Ahmedabad, Gujarat"` — what the search dropdown shows."""
        return f"{self.name}, {self.state}" if self.state else self.name


class SavedDestination(BaseModel):
    """
    Screen 12's saved destinations list.

    **Why this is in `geo` and not `accounts`:** City Search annotates `is_saved`
    with `Exists(SavedDestination.objects.filter(city=OuterRef("pk"), user=user))`.
    If the model lived in `accounts`, `geo` would have to import `accounts` and
    reverse the one-way import rule. Its endpoints are still served under
    `/users/me/saved-destinations/` — the URL prefix and the owning app are
    allowed to differ.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_destinations",
    )
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="saved_by")
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            # Scoped to live rows: a soft-deleted row still occupies its unique
            # key, so without the condition a user could never re-save a city
            # they had removed.
            models.UniqueConstraint(
                fields=["user", "city"],
                condition=models.Q(is_deleted=False),
                name="uniq_saved_destination_alive",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user_id} saved {self.city_id}"
