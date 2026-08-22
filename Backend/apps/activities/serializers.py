"""
activities — serializers. Owner: Dev A (models) · Dev B (endpoints).

Validation and shaping only. No cross-model writes, no calls into other apps.

`activities → geo` is a legal import direction (`LAYOUT.md` §5), so the nested
city shape is reused from `geo` rather than redeclared here.
"""

from rest_framework import serializers

from apps.activities.models import Activity, ActivityCategory
from apps.geo.serializers import CityMiniSerializer


class ActivityCategorySerializer(serializers.ModelSerializer):
    """`GET /activity-categories/` — Screen 8's filter chips."""

    class Meta:
        model = ActivityCategory
        fields = ("id", "name", "slug", "icon", "description")


class ActivityCategoryBriefSerializer(serializers.ModelSerializer):
    """The `{id, name, slug, icon}` shape nested inside an activity."""

    class Meta:
        model = ActivityCategory
        fields = ("id", "name", "slug", "icon")


class ActivitySerializer(serializers.ModelSerializer):
    """
    One row of **Activity Search** (Screen 8), and the detail body.

    The nested `category` and `city` need `select_related` upstream — see
    `selectors.activity_list`.
    """

    category = ActivityCategoryBriefSerializer(read_only=True)
    city = CityMiniSerializer(read_only=True)

    class Meta:
        model = Activity
        fields = (
            "id",
            "name",
            "description",
            "activity_type",
            "category",
            "city",
            "cost",
            "currency",
            "duration_minutes",
            "rating",
            "popularity_score",
            "image_url",
        )


# ---------------------------------------------------------------------- admin


class AdminActivityCategorySerializer(serializers.ModelSerializer):
    """`/admin/activity-categories/` — the read shape, made writable."""

    class Meta:
        model = ActivityCategory
        fields = (
            "id",
            "name",
            "slug",
            "icon",
            "description",
            "is_active",
            "is_deleted",
            "created_at",
        )
        read_only_fields = ("is_deleted", "created_at")


class AdminActivitySerializer(serializers.ModelSerializer):
    """
    `/admin/activities/` — full CRUD over the catalog.

    ⚠️ Editing `cost` here changes **only** the catalog. Every `TripActivity`
    already added keeps its snapshot, by design (trap #5): a curator fixing a
    price must not silently rewrite budgets users have already seen.

    `popularity_score` is read-only — it is a counter, not a field.
    """

    category_name = serializers.CharField(source="category.name", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True, default=None)

    class Meta:
        model = Activity
        fields = (
            "id",
            "city",
            "city_name",
            "category",
            "category_name",
            "name",
            "description",
            "activity_type",
            "cost",
            "currency",
            "duration_minutes",
            "rating",
            "image_url",
            "popularity_score",
            "is_active",
            "is_deleted",
            "created_at",
        )
        read_only_fields = ("popularity_score", "is_deleted", "created_at")
