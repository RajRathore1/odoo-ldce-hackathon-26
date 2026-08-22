"""
trips — serializers. Owner: Dev A.

Validation and shaping only. No cross-model writes, no calls into other apps.

Read and write shapes are **separate classes** — `TripListSerializer` is not
`TripCreateSerializer` with a `context` flag. One serializer that branches on
context is how a write field ends up readable on a public endpoint.
"""

from rest_framework import serializers

from apps.trips.models import Trip
from apps.trips.selectors import ZERO_COST_SUMMARY


def _stops(trip):
    """
    The trip's prefetched stops, or `None` when there is no relation to read.

    `getattr` rather than `trip.stops` because this module is written against
    both A3 (no `TripStop` table yet) and A4 (stops prefetched by the selector).
    """
    return getattr(trip, "stops", None)


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
        stops = _stops(trip)
        return 0 if stops is None else len(stops.all())

    def get_activities_count(self, trip) -> int:
        """From the selector's annotation. 0 until task A4 adds it."""
        return getattr(trip, "activities_count", 0)

    def get_cities(self, trip) -> list[str]:
        """City names in stop order — the "Bir · Manali · Kasol" line on a card."""
        stops = _stops(trip)
        if stops is None:
            return []
        return [stop.city.name for stop in stops.all() if stop.city_id]

    def get_estimated_cost(self, trip) -> str:
        """Money as a string, like every other amount in the API."""
        return str(self._cost(trip)["grand_total"])

    def get_is_over_budget(self, trip) -> bool:
        return bool(self._cost(trip)["is_over_budget"])


class TripDetailSerializer(TripListSerializer):
    """
    `GET /trips/{id}/`, and the body returned after a create or an update.

    Adds the fields only the owner has any use for. `share_token` is here and
    **not** on the list: a list is a page of tokens, which is a page of live
    share links, and nothing on Screen 6 needs them.
    """

    class Meta(TripListSerializer.Meta):
        fields = (
            *TripListSerializer.Meta.fields,
            "share_token",
            "views_count",
            "copied_from",
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
