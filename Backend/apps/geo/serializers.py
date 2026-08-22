"""
geo — serializers. Owner: models: Dev A · endpoints: Dev B.

Validation and shaping only. No cross-model writes, no calls into other apps.

⚠️ This app imports **nothing but `core`** (`LAYOUT.md` §5). `activities`
already imports `geo`, so importing it back would close a cycle — which is why
`CityActivitySerializer` below declares the activity fields by hand instead of
reusing the one in `activities`. The reverse accessor `city.activities` exists
without an import, because the FK is declared on the other side.
"""

from rest_framework import serializers

from apps.geo.models import City, Country, SavedDestination


class CountryBriefSerializer(serializers.ModelSerializer):
    """The `{id, name, iso2, flag_emoji}` shape nested inside a city."""

    class Meta:
        model = Country
        fields = ("id", "name", "iso2", "flag_emoji")


class CountrySerializer(serializers.ModelSerializer):
    """`GET /countries/` — the registration and city-search dropdowns."""

    class Meta:
        model = Country
        fields = ("id", "name", "iso2", "iso3", "region", "currency_code", "flag_emoji")


class CityMiniSerializer(serializers.ModelSerializer):
    """
    The `{id, name, country_name, image_url}` shape nested inside a trip stop.

    Needs `select_related("country")` upstream, or `country_name` is a query per
    row.
    """

    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = City
        fields = ("id", "name", "state", "country_name", "image_url")


class CityListSerializer(serializers.ModelSerializer):
    """
    One row of **City Search** (Screen 7).

    `activities_count` and `is_saved` are annotations from `selectors.city_list`
    — never per-row queries. `is_saved` lets the frontend draw the bookmark
    without a second call.
    """

    country = CountryBriefSerializer(read_only=True)
    region = serializers.CharField(source="country.region", read_only=True)
    activities_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = (
            "id",
            "name",
            "state",
            "country",
            "region",
            "cost_index",
            "avg_daily_cost",
            "currency",
            "popularity_score",
            "image_url",
            "activities_count",
            "is_saved",
        )

    def get_activities_count(self, city) -> int:
        return getattr(city, "activities_count", 0)

    def get_is_saved(self, city) -> bool:
        return bool(getattr(city, "is_saved", False))


class CityActivitySerializer(serializers.Serializer):
    """
    The top activities on a city detail page.

    Declared here rather than imported from `apps.activities.serializers`: that
    would make `geo` depend on `activities`, which already depends on `geo`.
    Read off the reverse accessor, which needs no import.
    """

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    activity_type = serializers.CharField(read_only=True)
    cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    currency = serializers.CharField(read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    rating = serializers.DecimalField(max_digits=2, decimal_places=1, read_only=True)
    image_url = serializers.CharField(read_only=True)


class CityDetailSerializer(CityListSerializer):
    """`GET /cities/{id}/` — the list row plus the map fields and top activities."""

    top_activities = CityActivitySerializer(many=True, read_only=True)

    class Meta(CityListSerializer.Meta):
        fields = (
            *CityListSerializer.Meta.fields,
            "description",
            "latitude",
            "longitude",
            "timezone",
            "top_activities",
        )


class SavedDestinationSerializer(serializers.ModelSerializer):
    """`GET /users/me/saved-destinations/`."""

    city = CityMiniSerializer(read_only=True)

    class Meta:
        model = SavedDestination
        fields = ("id", "city", "note", "created_at")


class SavedDestinationWriteSerializer(serializers.ModelSerializer):
    """`POST /users/me/saved-destinations/` — `city`* and an optional `note`."""

    class Meta:
        model = SavedDestination
        fields = ("city", "note")


# ---------------------------------------------------------------------- admin


class AdminCountrySerializer(serializers.ModelSerializer):
    """
    `/admin/countries/` — the same fields as the read serializer, **writable**.

    The user-facing `CountrySerializer` has no write path at all, which is the
    point of the split: exposing writes is an admin decision, not a flag on a
    shared class.
    """

    class Meta:
        model = Country
        fields = (
            "id",
            "name",
            "iso2",
            "iso3",
            "region",
            "currency_code",
            "flag_emoji",
            "is_active",
            "is_deleted",
            "created_at",
        )
        read_only_fields = ("is_deleted", "created_at")


class AdminCitySerializer(serializers.ModelSerializer):
    """
    `/admin/cities/`.

    `popularity_score` is read-only even here: it is a denormalised counter
    maintained by `trips.services.create_stop` and rebuilt by
    `manage.py recalc_popularity`. Letting an admin type over it would make the
    "popular destinations" list disagree with the trips behind it.
    """

    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = City
        fields = (
            "id",
            "country",
            "country_name",
            "name",
            "state",
            "latitude",
            "longitude",
            "timezone",
            "cost_index",
            "avg_daily_cost",
            "currency",
            "description",
            "image_url",
            "popularity_score",
            "is_active",
            "is_deleted",
            "created_at",
        )
        read_only_fields = ("popularity_score", "is_deleted", "created_at")
