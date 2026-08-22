"""
trips — models. Owner: Dev A.

`Trip`, `TripStop`, `TripActivity` — see docs/MODELS.md §6.

`Trip` is the root of the whole domain: stops hang off it, trip activities hang
off stops, expenses point at it. Everything the user builds on Screens 3-11 is
reachable from one `Trip` row.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.trips.constants import EXPLICIT_STATUSES, TripStatus
from core.models import BaseModel, OrderedModel
from core.utils import build_share_url, days_inclusive


class Trip(BaseModel):
    """
    One user's multi-city plan.

    Two fields are worth reading the comments on: `status`, which is stored
    rather than computed, and `share_token`, which is the only UUID in the
    project (decision D2).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trips",
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    start_date = models.DateField()
    end_date = models.DateField()

    # Stored, not computed — so `?status=ONGOING` stays an index scan instead of
    # a date expression over every row. Re-synced in `save()`; see the trap in
    # that method.
    status = models.CharField(
        max_length=10,
        choices=TripStatus.choices,
        default=TripStatus.PLANNED,
        db_index=True,
    )

    cover_photo = models.ImageField(upload_to="trips/covers/", null=True, blank=True)

    # Optional: plenty of users plan a trip without setting a target. `null`
    # means "no budget set", which is not the same as a budget of zero — the
    # budget endpoint returns `remaining: null` for the former.
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # One currency per trip; stops, activities and expenses inherit it. No FX
    # conversion anywhere in this project.
    currency = models.CharField(max_length=3, default="INR")

    is_public = models.BooleanField(default=False)
    # UUID rather than the integer pk: a share link must not be guessable, and
    # regenerating it has to kill the old link (task A7.1).
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    views_count = models.PositiveIntegerField(default=0)

    # Set by "Copy Trip" (task A7.3). SET_NULL: deleting the original must not
    # take everybody's copies with it.
    copied_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="copies",
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gte=models.F("start_date")),
                name="trip_end_date_gte_start_date",
            ),
        ]
        indexes = [
            # Screen 6 is always "my trips, filtered by tab".
            models.Index(fields=["user", "status"], name="trip_user_status_idx"),
            models.Index(fields=["user", "-created_at"], name="trip_user_created_idx"),
            models.Index(fields=["start_date"], name="trip_start_date_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    # ------------------------------------------------------------------ status

    @staticmethod
    def status_from_dates(start_date, end_date, today=None) -> str:
        """
        The status a trip's dates imply. Pure — no DB, no `self`.

        Separate from `save()` so it can be tested directly and reused when
        copying a trip.
        """
        if start_date is None or end_date is None:
            return TripStatus.PLANNED
        today = today or timezone.localdate()
        if end_date < today:
            return TripStatus.COMPLETED
        if start_date > today:
            return TripStatus.PLANNED
        return TripStatus.ONGOING

    def save(self, *args, **kwargs):
        """
        Keep `status` in step with the dates.

        ⚠️ `DRAFT` and `CANCELLED` are states the *user* chose, so a date sync
        must never overwrite them (`CLAUDE.md` trap #4). Everything else is
        derived, which is what lets `status` be a stored, indexed column.

        When a caller passes `update_fields`, `status` is appended to it — the
        alternative is an object whose in-memory status disagrees with the row
        it was just written from.
        """
        if self.status not in EXPLICIT_STATUSES:
            self.status = self.status_from_dates(self.start_date, self.end_date)
            update_fields = kwargs.get("update_fields")
            if update_fields is not None and "status" not in update_fields:
                kwargs["update_fields"] = [*update_fields, "status"]
        super().save(*args, **kwargs)

    # -------------------------------------------------------------- properties

    @property
    def duration_days(self) -> int:
        """Both ends counted — the 1st to the 3rd is three days, not two."""
        return days_inclusive(self.start_date, self.end_date)

    @property
    def share_url(self) -> str:
        """Frontend link, not an API path. Valid whether or not the trip is public."""
        return build_share_url(self.share_token)


class TripStop(BaseModel, OrderedModel):
    """
    One city, for one date range, inside a trip. The "sections" of Screen 5.

    ⚠️ **No `UniqueConstraint(trip, order)`** — SQLite has no deferred
    constraints, so a drag-to-reorder would collide half way through the update
    (`CLAUDE.md` trap #2). Uniqueness of `order` is maintained by the single
    `bulk_update` in `services.reorder_stops`, not by the database.
    """

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="stops")
    city = models.ForeignKey(
        "geo.City",
        # PROTECT: a city that somebody's itinerary points at must not be
        # deletable out from under them.
        on_delete=models.PROTECT,
        related_name="trip_stops",
    )

    # Defaults to the city name — see `services.create_stop`. Editable because
    # "Bir" and "Bir (paragliding)" are both reasonable section headings.
    title = models.CharField(max_length=120, blank=True)

    start_date = models.DateField()
    end_date = models.DateField()

    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta(OrderedModel.Meta):
        # Explicit, because Django would otherwise resolve `Meta` up the MRO to
        # `BaseModel.Meta` and silently lose the ordering — see `OrderedModel`.
        abstract = False
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gte=models.F("start_date")),
                name="tripstop_end_date_gte_start_date",
            ),
        ]
        indexes = [
            models.Index(fields=["trip", "order"], name="tripstop_trip_order_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.display_title} ({self.trip_id})"

    @property
    def display_title(self) -> str:
        """What the section header shows. Falls back to the city name."""
        return self.title or (self.city.name if self.city_id else "")

    @property
    def nights(self) -> int:
        """
        Nights, not days — arriving on the 18th and leaving on the 21st is three
        nights. This is the one place in the project where a range is *not*
        counted inclusively, because that is what a hotel booking means.
        """
        if self.start_date is None or self.end_date is None:
            return 0
        return max((self.end_date - self.start_date).days, 0)


class TripActivity(BaseModel, OrderedModel):
    """
    One activity placed in one trip, on one day.

    Not the same thing as the catalog `activities.Activity`: `cost`, `currency`
    and `duration_minutes` are **snapshotted** off the catalog row when the
    activity is added, so editing the catalog later cannot rewrite somebody's
    saved budget (`CLAUDE.md` trap #5).

    Either it points at a catalog activity **or** it carries a `custom_title` —
    never both, never neither. Enforced in the serializer for a readable 400,
    and in the database because a bad row here corrupts the budget.
    """

    trip_stop = models.ForeignKey(
        TripStop, on_delete=models.CASCADE, related_name="activities"
    )
    activity = models.ForeignKey(
        "activities.Activity",
        # PROTECT rather than SET_NULL: nulling the FK on a row that has no
        # `custom_title` would violate the constraint below, turning a catalog
        # tidy-up into an IntegrityError instead of a clean refusal.
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="trip_activities",
    )
    custom_title = models.CharField(max_length=150, blank=True)

    day_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="INR")
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta(OrderedModel.Meta):
        abstract = False
        constraints = [
            models.CheckConstraint(
                check=(models.Q(activity__isnull=False) & models.Q(custom_title=""))
                | (models.Q(activity__isnull=True) & ~models.Q(custom_title="")),
                name="tripactivity_catalog_xor_custom",
            ),
        ]
        indexes = [
            # The itinerary and the calendar both read a whole stop in day order.
            models.Index(
                fields=["trip_stop", "day_date", "order"],
                name="tripactivity_day_order_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} on {self.day_date}"

    @property
    def title(self) -> str:
        """The catalog name, or the user's own wording for a custom entry."""
        if self.custom_title:
            return self.custom_title
        return self.activity.name if self.activity_id else ""

    @property
    def activity_type(self) -> str | None:
        """`None` for a custom entry — there is no catalog row to classify it."""
        return self.activity.activity_type if self.activity_id else None
