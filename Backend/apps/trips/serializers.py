"""
trips — serializers. Owner: Dev A.

Validation and shaping only. No cross-model writes, no calls into other apps.

Read and write shapes are **separate classes** — `TripListSerializer` is not
`TripWriteSerializer` with a `context` flag. One serializer that branches on
context is how a write field ends up readable on a public endpoint.

Ordered inner-most first: activities, then stops, then the trip that nests
them, so every nested serializer is a real reference rather than a lazy lookup.
"""

from rest_framework import serializers

from apps.geo.serializers import CityMiniSerializer
from apps.trips.models import Trip, TripActivity, TripStop
from apps.trips.selectors import ZERO_COST_SUMMARY


def _validate_times(start_time, end_time) -> None:
    """`end_time` after `start_time`, when both are given."""
    if start_time and end_time and end_time <= start_time:
        raise serializers.ValidationError(
            {"end_time": "End time must be after the start time."}
        )


# ------------------------------------------------------------ trip activities


class TripActivitySerializer(serializers.ModelSerializer):
    """
    One activity as it sits in an itinerary.

    `title` and `activity_type` come off the model's properties, which read the
    catalog row for a linked activity and fall back to the user's own wording
    for a custom entry. Needs `select_related("activity")` upstream.
    """

    title = serializers.CharField(read_only=True)
    activity_id = serializers.IntegerField(read_only=True)
    activity_type = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = TripActivity
        fields = (
            "id",
            "trip_stop",
            "title",
            "activity_id",
            "activity_type",
            "day_date",
            "start_time",
            "end_time",
            "duration_minutes",
            "cost",
            "currency",
            "order",
            "notes",
        )


class TripActivityCreateSerializer(serializers.ModelSerializer):
    """
    `POST /trips/{id}/stops/{sid}/activities/`.

    `currency` is not accepted: a trip has one currency and its children inherit
    it (`CLAUDE.md` §4). Taking the catalog row's currency instead would let one
    trip hold two of them, and the budget sums children without converting.

    `cost` is optional — when it is omitted and `activity` is given, the service
    snapshots it off the catalog.
    """

    class Meta:
        model = TripActivity
        fields = (
            "activity",
            "custom_title",
            "day_date",
            "start_time",
            "end_time",
            "cost",
            "duration_minutes",
            "notes",
        )

    def validate(self, attrs: dict) -> dict:
        activity = attrs.get("activity")
        custom_title = (attrs.get("custom_title") or "").strip()

        if bool(activity) == bool(custom_title):
            raise serializers.ValidationError(
                {
                    "custom_title": (
                        "Provide either `activity` (a catalog id) or `custom_title`, "
                        "not both and not neither."
                    )
                }
            )
        attrs["custom_title"] = custom_title

        stop = self.context["stop"]
        if not stop.start_date <= attrs["day_date"] <= stop.end_date:
            raise serializers.ValidationError(
                {
                    "day_date": (
                        f"This day is outside the stop's dates "
                        f"({stop.start_date} to {stop.end_date})."
                    )
                }
            )
        _validate_times(attrs.get("start_time"), attrs.get("end_time"))
        return attrs


class TripActivityUpdateSerializer(serializers.ModelSerializer):
    """
    `PATCH /trip-activities/{id}/` — time, cost, day and order.

    `activity` and `custom_title` are deliberately absent: swapping one for the
    other is a different activity, and allowing it here is how a row ends up
    with both or neither and trips the database constraint.
    """

    class Meta:
        model = TripActivity
        fields = (
            "day_date",
            "start_time",
            "end_time",
            "cost",
            "duration_minutes",
            "order",
            "notes",
        )

    def validate(self, attrs: dict) -> dict:
        stop = self.instance.trip_stop
        day_date = attrs.get("day_date", self.instance.day_date)

        if not stop.start_date <= day_date <= stop.end_date:
            raise serializers.ValidationError(
                {
                    "day_date": (
                        f"This day is outside the stop's dates "
                        f"({stop.start_date} to {stop.end_date}). Use the reorder "
                        f"endpoint to move an activity to another stop."
                    )
                }
            )
        _validate_times(
            attrs.get("start_time", self.instance.start_time),
            attrs.get("end_time", self.instance.end_time),
        )
        return attrs


# ---------------------------------------------------------------------- stops


class TripStopSerializer(serializers.ModelSerializer):
    """One section of Screen 5. `title` falls back to the city name."""

    title = serializers.CharField(source="display_title", read_only=True)
    city = CityMiniSerializer(read_only=True)
    nights = serializers.IntegerField(read_only=True)
    activities_count = serializers.SerializerMethodField()

    class Meta:
        model = TripStop
        fields = (
            "id",
            "title",
            "city",
            "start_date",
            "end_date",
            "nights",
            "order",
            "budget",
            "activities_count",
            "notes",
        )

    def get_activities_count(self, stop) -> int:
        """The selector's annotation, or the prefetch — never a query per row."""
        annotated = getattr(stop, "activities_count", None)
        if annotated is not None:
            return annotated
        return len(stop.activities.all())


class TripStopWithActivitiesSerializer(TripStopSerializer):
    """The stop as it appears nested in `GET /trips/{id}/`."""

    activities = TripActivitySerializer(many=True, read_only=True)

    class Meta(TripStopSerializer.Meta):
        fields = (*TripStopSerializer.Meta.fields, "activities")


class TripStopWriteSerializer(serializers.ModelSerializer):
    """
    `POST /trips/{id}/stops/` and `PATCH /trips/{id}/stops/{sid}/`.

    `order` is not accepted — it is assigned server-side on create and changed
    only through the reorder endpoint, which is the one place that can keep the
    whole sequence consistent in a single statement.
    """

    class Meta:
        model = TripStop
        fields = ("city", "title", "start_date", "end_date", "budget", "notes")

    def validate(self, attrs: dict) -> dict:
        """The stop's range has to sit inside the trip's range."""
        trip = self.context["trip"]
        start_date = attrs.get("start_date") or getattr(self.instance, "start_date", None)
        end_date = attrs.get("end_date") or getattr(self.instance, "end_date", None)

        if end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "End date must be on or after the start date."}
            )
        if start_date < trip.start_date or end_date > trip.end_date:
            raise serializers.ValidationError(
                {
                    "start_date": (
                        f"A stop must sit inside the trip's dates "
                        f"({trip.start_date} to {trip.end_date})."
                    )
                }
            )
        return attrs


# -------------------------------------------------------------------- reorder


class StopReorderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField(min_value=1)


class StopReorderSerializer(serializers.Serializer):
    """`POST /trips/{id}/stops/reorder/` — `{"items": [{"id": 91, "order": 1}]}`."""

    items = StopReorderItemSerializer(many=True, allow_empty=False)


class ActivityReorderItemSerializer(serializers.Serializer):
    """
    `trip_stop` and `day_date` are optional: dragging inside one day sends
    neither, dragging onto another day or another stop sends what changed.
    """

    id = serializers.IntegerField()
    order = serializers.IntegerField(min_value=1)
    day_date = serializers.DateField(required=False)
    trip_stop = serializers.IntegerField(required=False)


class ActivityReorderSerializer(serializers.Serializer):
    """`POST /trips/{id}/activities/reorder/` — also moves across days and stops."""

    items = ActivityReorderItemSerializer(many=True, allow_empty=False)


# ---------------------------------------------------------------------- trips


class TripListSerializer(serializers.ModelSerializer):
    """
    One row of **My Trips** (Screen 6).

    Every aggregate here is flat — no nesting, no per-row queries. `stops_count`
    and `cities` come off the selector's prefetch, `activities_count` off its
    annotation, and the two cost figures off a single bulk lookup passed in
    through `context["cost_summaries"]`.
    """

    duration_days = serializers.IntegerField(read_only=True)
    share_url = serializers.CharField(read_only=True)
    stops_count = serializers.SerializerMethodField()
    activities_count = serializers.SerializerMethodField()
    cities = serializers.SerializerMethodField()
    estimated_cost = serializers.SerializerMethodField()
    is_over_budget = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = (
            "id",
            "name",
            "description",
            "start_date",
            "end_date",
            "duration_days",
            "status",
            "cover_photo",
            "stops_count",
            "activities_count",
            "cities",
            "total_budget",
            "estimated_cost",
            "currency",
            "is_over_budget",
            "is_public",
            "share_url",
            "created_at",
        )

    def _cost(self, trip) -> dict:
        """This trip's row out of the page-wide bulk cost lookup."""
        return self.context.get("cost_summaries", {}).get(trip.pk, ZERO_COST_SUMMARY)

    def get_stops_count(self, trip) -> int:
        """
        Counted off the prefetch, never queried per row.

        There is deliberately **no `Trip.stops_count` property**: a property and
        a queryset annotation of the same name cannot coexist (Django assigns
        annotations with `setattr`, which a property with no setter rejects),
        and two ways to derive one number is how screens start disagreeing.
        """
        return len(trip.stops.all())

    def get_activities_count(self, trip) -> int:
        """From the selector's annotation."""
        return getattr(trip, "activities_count", 0)

    def get_cities(self, trip) -> list[str]:
        """City names in stop order — the "Bir · Manali · Kasol" line on a card."""
        return [stop.city.name for stop in trip.stops.all() if stop.city_id]

    def get_estimated_cost(self, trip) -> str:
        """Money as a string, like every other amount in the API."""
        return str(self._cost(trip)["grand_total"])

    def get_is_over_budget(self, trip) -> bool:
        return bool(self._cost(trip)["is_over_budget"])


class TripDetailSerializer(TripListSerializer):
    """
    `GET /trips/{id}/`, and the body returned after a create or an update.

    Adds the nested itinerary and the fields only the owner has any use for.
    `share_token` is here and **not** on the list: a list is a page of tokens,
    which is a page of live share links, and nothing on Screen 6 needs them.
    """

    stops = TripStopWithActivitiesSerializer(many=True, read_only=True)

    class Meta(TripListSerializer.Meta):
        fields = (
            *TripListSerializer.Meta.fields,
            "share_token",
            "views_count",
            "copied_from",
            "stops",
            "updated_at",
        )


class TripWriteSerializer(serializers.ModelSerializer):
    """
    `POST /trips/` and `PATCH /trips/{id}/`.

    Named `Write` rather than `Create` because `PATCH` uses it too — the write
    shape is identical, and a second near-identical class would be one more
    place to forget a validation rule.

    `is_public` is **not** writable here: sharing has its own endpoints
    (`POST|DELETE /trips/{id}/share/`), and two ways to publish a trip is two
    places to get the permission check wrong.

    `status` accepts `DRAFT` and `CANCELLED`. The other three are derived from
    the dates by `Trip.save()`, so sending them is silently ignored rather than
    rejected — see `CLAUDE.md` trap #4.
    """

    class Meta:
        model = Trip
        fields = (
            "name",
            "description",
            "start_date",
            "end_date",
            "status",
            "total_budget",
            "currency",
            "cover_photo",
        )

    def validate_currency(self, value: str) -> str:
        """Normalised so `"inr"` and `"INR"` cannot both end up in the table."""
        return value.upper()

    def validate(self, attrs: dict) -> dict:
        """
        `end_date >= start_date`, checked against the merged instance so a
        `PATCH` that moves only one of the two dates is still validated.

        A `start_date` in the past is allowed on purpose: users log trips they
        have already taken.
        """
        start_date = attrs.get("start_date") or getattr(self.instance, "start_date", None)
        end_date = attrs.get("end_date") or getattr(self.instance, "end_date", None)

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "End date must be on or after the start date."}
            )
        return attrs


class CoverPhotoSerializer(serializers.ModelSerializer):
    """`POST /trips/{id}/cover-photo/` — `multipart/form-data`, field `cover_photo`."""

    cover_photo = serializers.ImageField(required=True)

    class Meta:
        model = Trip
        fields = ("cover_photo",)
