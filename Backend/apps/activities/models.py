"""
activities — models. Owner: **Dev A** (models) · **Dev B** (endpoints).

`ActivityCategory`, `Activity` — see docs/MODELS.md §5.

`Activity` is the **master catalog**. It is not the same thing as
`trips.TripActivity`, which is one catalog activity placed into one trip on one
day. When a user adds an activity to a trip, the cost is **copied** onto the
`TripActivity` row — editing this catalog later must never silently rewrite
somebody's saved budget.
"""

from django.db import models

from apps.activities.constants import ActivityType
from core.models import BaseModel


class ActivityCategory(BaseModel):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=40, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "activity categories"

    def __str__(self) -> str:
        return self.name


class Activity(BaseModel):
    city = models.ForeignKey(
        "geo.City",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="activities",
        help_text="Null means generic — available in any city.",
    )
    category = models.ForeignKey(
        ActivityCategory,
        # SET_NULL: deleting a category must not delete the activities in it.
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
    )
    name = models.CharField(max_length=150, db_index=True)
    description = models.TextField(blank=True)
    activity_type = models.CharField(
        max_length=20, choices=ActivityType.choices, db_index=True
    )

    # Indicative, per person. Snapshotted onto TripActivity.cost when added.
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="INR")
    duration_minutes = models.PositiveIntegerField(default=60)

    image_url = models.URLField(blank=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)

    # Denormalised TripActivity count — see City.popularity_score.
    popularity_score = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-popularity_score", "name")
        verbose_name_plural = "activities"
        indexes = [
            models.Index(fields=["city", "activity_type"], name="activity_city_type_idx"),
            models.Index(fields=["-popularity_score"], name="activity_popularity_idx"),
        ]

    def __str__(self) -> str:
        return self.name
