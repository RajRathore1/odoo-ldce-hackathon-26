"""Read-only serializers for the city and activity catalogue."""

from rest_framework import serializers

from .models import Activity, City, Country


class CountrySlimSerializer(serializers.ModelSerializer):
    """Nested country representation used inside city payloads."""

    class Meta:
        model = Country
        fields = ["id", "name", "code2", "continent"]


class CitySlimSerializer(serializers.ModelSerializer):
    """Nested city representation used inside activity payloads."""

    class Meta:
        model = City
        fields = ["id", "name", "display_name"]


class CitySerializer(serializers.ModelSerializer):
    """City list row: enough meta info for the City Search results."""

    country = CountrySlimSerializer(read_only=True)
    region = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = City
        fields = [
            "id",
            "name",
            "display_name",
            "slug",
            "country",
            "region",
            "latitude",
            "longitude",
            "population",
            "cost_index",
            "popularity",
            "image",
        ]


class CityDetailSerializer(CitySerializer):
    """City detail: adds the blurb and a count of bookable activities."""

    activity_count = serializers.IntegerField(read_only=True)

    class Meta(CitySerializer.Meta):
        fields = CitySerializer.Meta.fields + ["blurb", "activity_count", "timezone"]


class ActivitySerializer(serializers.ModelSerializer):
    """Activity row for Activity Search, including its parent city."""

    city = CitySlimSerializer(read_only=True)
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )

    class Meta:
        model = Activity
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "category_display",
            "description",
            "cost",
            "duration_minutes",
            "image",
            "popularity",
            "city",
        ]
