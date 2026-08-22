"""
geo — serializers. Owner: models: Dev A · endpoints: Dev B.

Validation and shaping only. No cross-model writes, no calls into other apps.
"""

from rest_framework import serializers

from apps.geo.models import City


class CityMiniSerializer(serializers.ModelSerializer):
    """
    The `{id, name, country_name, image_url}` shape nested inside a trip stop.

    Lives here rather than in `trips` because `trips → geo` is the legal import
    direction and the city catalog owns its own read shapes. Needs
    `select_related("country")` upstream, or `country_name` is a query per row.
    """

    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = City
        fields = ("id", "name", "state", "country_name", "image_url")
