"""Read-only catalogue endpoints.

Public on purpose: the City/Activity search screens are browsable before the
user signs in, so these override the project-wide IsAuthenticated default.
"""

from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from .filters import ActivityFilter, CityFilter
from .models import Activity, City
from .serializers import ActivitySerializer, CityDetailSerializer, CitySerializer


@extend_schema_view(
    list=extend_schema(
        summary="Search cities",
        description=(
            "Browsable city catalogue behind the City Search screen.\n\n"
            "`search` matches the transliterated city+country name, so "
            "`zurich`, `Zürich` and `zurich switzerland` all work.\n\n"
            "`cost_index` is a 1.0-5.0 daily-budget tier and is null for "
            "cities outside the curated set."
        ),
        tags=["Geo"],
        examples=[
            OpenApiExample(
                "Cheap European cities, most popular first",
                value="?continent=EU&cost_index_max=2.5&ordering=-popularity",
                request_only=True,
            )
        ],
    ),
    retrieve=extend_schema(
        summary="Get a city",
        description="Adds the city blurb and a count of its bookable activities.",
        tags=["Geo"],
    ),
)
class CityViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    filterset_class = CityFilter
    # search_names is a ToSearchTextField: cities_light registers an icontains
    # lookup on it that normalises the query, so no manual to_search() needed.
    search_fields = ["search_names"]
    ordering_fields = ["popularity", "population", "name", "cost_index"]
    ordering = ["-popularity", "name"]

    def get_queryset(self):
        queryset = City.objects.select_related("country", "region")
        if self.action == "retrieve":
            queryset = queryset.annotate(
                activity_count=Count(
                    "activities", filter=Q(activities__is_active=True)
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CityDetailSerializer
        return CitySerializer


@extend_schema_view(
    list=extend_schema(
        summary="Search activities",
        description=(
            "Things to do, filterable by city, category, cost and duration "
            "for the Activity Search screen."
        ),
        tags=["Geo"],
        examples=[
            OpenApiExample(
                "Food activities under 50, short first",
                value="?category=food&cost_max=50&ordering=duration_minutes",
                request_only=True,
            )
        ],
    ),
    retrieve=extend_schema(summary="Get an activity", tags=["Geo"]),
)
class ActivityViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ActivitySerializer
    filterset_class = ActivityFilter
    search_fields = ["name", "description", "city__name"]
    ordering_fields = ["cost", "popularity", "duration_minutes", "name"]
    ordering = ["-popularity", "name"]

    def get_queryset(self):
        return Activity.objects.filter(is_active=True).select_related(
            "city", "city__country"
        )
