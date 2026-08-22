"""
activities — views. Owner: Dev A (models) · Dev B (endpoints).

Thin. Parse the request, call a service or selector, return a response.
No business rules and no multi-step ORM work.
"""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.viewsets import ModelViewSet

from apps.activities import selectors
from apps.activities.filters import (
    ActivityFilterSet,
    AdminActivityCategoryFilterSet,
    AdminActivityFilterSet,
)
from apps.activities.models import Activity, ActivityCategory
from apps.activities.serializers import (
    ActivityCategorySerializer,
    ActivitySerializer,
    AdminActivityCategorySerializer,
    AdminActivitySerializer,
)
from core.mixins import AdminOnlyMixin, UnfilteredObjectMixin
from core.pagination import LargePagination

DEFAULT_POPULAR_LIMIT = 10
MAX_POPULAR_LIMIT = 50


@extend_schema(tags=["activities"])
class ActivityCategoryListView(generics.ListAPIView):
    """
    `GET /activity-categories/` — the filter chips on Screen 8.

    **Not paginated:** a small fixed set, and the chips are rendered all at once.
    """

    serializer_class = ActivityCategorySerializer
    pagination_class = None
    filter_backends: list = []

    def get_queryset(self):
        return selectors.category_list()


@extend_schema(tags=["activities"])
class ActivityListView(generics.ListAPIView):
    """
    `GET /activities/` — Activity Search (Screen 8).

    `LargePagination` for the same reason as City Search: this is a catalog
    somebody is scrolling, not a page of results they will read.
    """

    serializer_class = ActivitySerializer
    pagination_class = LargePagination
    filterset_class = ActivityFilterSet
    search_fields = ("name", "description")
    ordering_fields = ("popularity_score", "cost", "duration_minutes", "rating", "name")
    ordering = ("-popularity_score", "name")

    def get_queryset(self):
        return selectors.activity_list()


@extend_schema(tags=["activities"])
class ActivityDetailView(generics.RetrieveAPIView):
    """`GET /activities/{id}/`."""

    serializer_class = ActivitySerializer

    def get_queryset(self):
        return selectors.activity_list()


@extend_schema(
    tags=["activities"],
    summary="Popular activities",
    parameters=[
        OpenApiParameter("city", int, description="Restrict to one city."),
        OpenApiParameter(
            "limit",
            int,
            description=f"Default {DEFAULT_POPULAR_LIMIT}, capped at {MAX_POPULAR_LIMIT}.",
        ),
    ],
    responses={200: ActivitySerializer(many=True)},
)
class PopularActivityListView(generics.ListAPIView):
    """`GET /activities/popular/` — `?city=` and `?limit=`. Bounded top-N, unpaginated."""

    serializer_class = ActivitySerializer
    pagination_class = None
    filter_backends: list = []

    def get_queryset(self):
        return selectors.popular_activities(city_id=self._city(), limit=self._limit())

    def _city(self) -> int | None:
        try:
            return int(self.request.query_params["city"])
        except (KeyError, TypeError, ValueError):
            return None

    def _limit(self) -> int:
        try:
            limit = int(self.request.query_params.get("limit", DEFAULT_POPULAR_LIMIT))
        except (TypeError, ValueError):
            return DEFAULT_POPULAR_LIMIT
        return max(1, min(limit, MAX_POPULAR_LIMIT))


# ---------------------------------------------------------------------- admin


@extend_schema(tags=["admin-master-data"])
class AdminActivityCategoryViewSet(AdminOnlyMixin, UnfilteredObjectMixin, ModelViewSet):
    """
    `/admin/activity-categories/` — full CRUD.

    Delete is soft, which is what makes it safe: `Activity.category` is
    `SET_NULL`, so a hard delete would quietly orphan every activity in the
    category.
    """

    serializer_class = AdminActivityCategorySerializer
    filterset_class = AdminActivityCategoryFilterSet
    search_fields = ("name", "slug")
    ordering_fields = ("name", "created_at")
    ordering = ("name",)

    def get_queryset(self):
        return ActivityCategory.all_objects.all()


@extend_schema(tags=["admin-master-data"])
class AdminActivityViewSet(AdminOnlyMixin, UnfilteredObjectMixin, ModelViewSet):
    """`/admin/activities/` — full CRUD over the catalog."""

    serializer_class = AdminActivitySerializer
    filterset_class = AdminActivityFilterSet
    search_fields = ("name", "description", "city__name")
    ordering_fields = ("name", "cost", "rating", "popularity_score", "created_at")
    ordering = ("-popularity_score", "name")

    def get_queryset(self):
        return Activity.all_objects.select_related("category", "city", "city__country")
