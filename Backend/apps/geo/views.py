"""
geo — views. Owner: models: Dev A · endpoints: Dev B.

Thin. Parse the request, call a service or selector, return a response.
No business rules and no multi-step ORM work.
"""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from apps.geo import selectors, services
from apps.geo.filters import (
    AdminCityFilterSet,
    AdminCountryFilterSet,
    CityFilterSet,
    CountryFilterSet,
)
from apps.geo.models import City, Country
from apps.geo.serializers import (
    AdminCitySerializer,
    AdminCountrySerializer,
    CityDetailSerializer,
    CityListSerializer,
    CountrySerializer,
    SavedDestinationSerializer,
    SavedDestinationWriteSerializer,
)
from core.mixins import AdminOnlyMixin, UnfilteredObjectMixin
from core.pagination import LargePagination
from core.response import created, no_content, success

#: `/cities/popular/` is a top-N, so it takes a `limit` rather than a page. The
#: ceiling stops `?limit=100000` turning a dashboard tile into a table scan.
DEFAULT_POPULAR_LIMIT = 10
MAX_POPULAR_LIMIT = 50


@extend_schema(tags=["geo"])
class CountryListView(generics.ListAPIView):
    """
    `GET /countries/` — the registration and city-search dropdowns.

    Paginated like every other list, but on `LargePagination`: there are about
    thirty countries, so a dropdown fills in one request.

    **`AllowAny`**, unlike the rest of the API: the registration form
    ([`API.md`](API.md) §2) accepts a `country` id, so the dropdown has to be
    fillable *before* the user has a token. Nothing here is private — it is a
    list of countries.
    """

    permission_classes = [AllowAny]
    serializer_class = CountrySerializer
    pagination_class = LargePagination
    filterset_class = CountryFilterSet
    search_fields = ("name", "iso2", "iso3")
    ordering_fields = ("name", "region")
    ordering = ("name",)

    def get_queryset(self):
        return selectors.country_list()


@extend_schema(tags=["geo"])
class CityListView(generics.ListAPIView):
    """
    `GET /cities/` — City Search (Screen 7).

    `LargePagination`: the user is scrolling a catalog looking for one row, so a
    bigger page means fewer round-trips.
    """

    serializer_class = CityListSerializer
    permission_classes = [AllowAny]
    pagination_class = LargePagination
    filterset_class = CityFilterSet
    search_fields = ("name", "state", "country__name")
    ordering_fields = ("popularity_score", "name", "cost_index", "avg_daily_cost")
    ordering = ("-popularity_score", "name")

    def get_queryset(self):
        return selectors.city_list(self.request.user)


@extend_schema(tags=["geo"])
class CityDetailView(generics.RetrieveAPIView):
    """`GET /cities/{id}/` — the search row plus map fields and top activities."""

    permission_classes = [AllowAny]
    serializer_class = CityDetailSerializer

    def get_queryset(self):
        return selectors.city_list(self.request.user)

    def retrieve(self, request, *args, **kwargs):
        city = self.get_object()
        # Attached rather than declared as a nested source, because the top-N
        # slice belongs to the selector, not to the serializer.
        city.top_activities = selectors.city_top_activities(city)
        return success(data=CityDetailSerializer(city).data)


@extend_schema(
    tags=["geo"],
    summary="Popular destinations",
    parameters=[
        OpenApiParameter(
            "limit",
            int,
            description=f"How many to return. Default {DEFAULT_POPULAR_LIMIT}, "
            f"capped at {MAX_POPULAR_LIMIT}.",
        )
    ],
    responses={200: CityListSerializer(many=True)},
)
class PopularCityListView(generics.ListAPIView):
    """
    `GET /cities/popular/` — the dashboard's recommendations.

    **Not paginated:** a bounded top-N, which is the one case the pagination
    convention exempts.
    """

    permission_classes = [AllowAny]
    serializer_class = CityListSerializer
    pagination_class = None
    filter_backends: list = []

    def get_queryset(self):
        return selectors.popular_cities(limit=self._limit(), user=self.request.user)

    def _limit(self) -> int:
        try:
            limit = int(self.request.query_params.get("limit", DEFAULT_POPULAR_LIMIT))
        except (TypeError, ValueError):
            return DEFAULT_POPULAR_LIMIT
        return max(1, min(limit, MAX_POPULAR_LIMIT))


@extend_schema(tags=["profile"])
class SavedDestinationListCreateView(generics.ListCreateAPIView):
    """
    `GET|POST /users/me/saved-destinations/` — Screen 12's bookmarks.

    Served under `/users/me/` but owned by `geo`, because City Search annotates
    `is_saved` off this model and `geo` may not import `accounts`
    ([`MODELS.md`](MODELS.md) §4).
    """

    def get_queryset(self):
        return selectors.saved_destinations(self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SavedDestinationWriteSerializer
        return SavedDestinationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        saved = services.save_destination(user=request.user, **serializer.validated_data)
        return created(
            data=SavedDestinationSerializer(saved).data, message="Destination saved."
        )


@extend_schema(tags=["profile"])
class SavedDestinationDestroyView(generics.DestroyAPIView):
    """`DELETE /users/me/saved-destinations/{id}/`."""

    serializer_class = SavedDestinationSerializer

    def get_queryset(self):
        return selectors.saved_destinations(self.request.user)

    def destroy(self, request, *args, **kwargs):
        services.remove_saved_destination(self.get_object())
        return no_content()


# ---------------------------------------------------------------------- admin


@extend_schema(tags=["admin-master-data"])
class AdminCountryViewSet(AdminOnlyMixin, UnfilteredObjectMixin, ModelViewSet):
    """
    `/admin/countries/` — full CRUD.

    Reads `all_objects` so a soft-deleted country is visible and restorable;
    `?include_deleted=true` reveals them. Delete is soft, which matters here:
    `City.country` is `PROTECT`, so hard-deleting a country in use would be
    refused outright.
    """

    serializer_class = AdminCountrySerializer
    filterset_class = AdminCountryFilterSet
    search_fields = ("name", "iso2", "iso3")
    ordering_fields = ("name", "region", "created_at")
    ordering = ("name",)

    def get_queryset(self):
        return Country.all_objects.all()


@extend_schema(tags=["admin-master-data"])
class AdminCityViewSet(AdminOnlyMixin, UnfilteredObjectMixin, ModelViewSet):
    """`/admin/cities/` — full CRUD."""

    serializer_class = AdminCitySerializer
    filterset_class = AdminCityFilterSet
    search_fields = ("name", "state", "country__name")
    ordering_fields = ("name", "popularity_score", "cost_index", "created_at")
    ordering = ("name",)

    def get_queryset(self):
        return City.all_objects.select_related("country")
