"""
trips — views. Owner: Dev A.

Thin. Parse the request, call a service or selector, return a response.
No business rules and no multi-step ORM work.
"""

from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.trips import selectors, services
from apps.trips.filters import AdminTripFilterSet, TripFilterSet
from apps.trips.models import Trip, TripStop
from apps.trips.serializers import (
    ActivityReorderSerializer,
    AdminTripSerializer,
    CoverPhotoSerializer,
    ItinerarySerializer,
    PublicTripSerializer,
    StopReorderSerializer,
    TripActivityCreateSerializer,
    TripActivitySerializer,
    TripActivityUpdateSerializer,
    TripCopySerializer,
    TripDetailSerializer,
    TripListSerializer,
    TripShareSerializer,
    TripStopSerializer,
    TripStopWriteSerializer,
    TripWriteSerializer,
)
from core.mixins import (
    AdminOnlyMixin,
    OwnerQuerysetMixin,
    SerializerActionMixin,
    UnfilteredObjectMixin,
)
from core.permissions import IsTripOwner
from core.response import created, no_content, success


class TripScopedMixin:
    """
    Resolve `trip_id` from the URL against the caller's **own** trips.

    A stranger's trip id is a 404 rather than a 403, for the same reason the
    trip list is owner-scoped: there is nothing worth confirming the existence
    of. Every nested route inherits this, so ownership is checked once, here,
    instead of in six views.
    """

    permission_classes = [IsAuthenticated]

    @cached_property
    def trip(self) -> Trip:
        return get_object_or_404(
            Trip.objects.filter(user=self.request.user), pk=self.kwargs["trip_id"]
        )

    def get_serializer_context(self) -> dict:
        return {**super().get_serializer_context(), "trip": self.trip}


class StopScopedMixin(TripScopedMixin):
    """Adds `stop_id`, resolved against the trip that `TripScopedMixin` found."""

    @cached_property
    def stop(self) -> TripStop:
        return get_object_or_404(
            TripStop.objects.filter(trip=self.trip), pk=self.kwargs["stop_id"]
        )

    def get_serializer_context(self) -> dict:
        return {**super().get_serializer_context(), "stop": self.stop}


# ---------------------------------------------------------------------- trips


@extend_schema(tags=["trips"])
class TripViewSet(OwnerQuerysetMixin, SerializerActionMixin, ModelViewSet):
    """
    `/trips/` — the caller's own trips.

    `OwnerQuerysetMixin` scopes the queryset, so somebody else's trip is a 404
    rather than a 403: a list cannot be filtered by a permission class, and
    there is no reason to confirm that a stranger's trip id exists.
    `IsTripOwner` stays on as the second line of defence for detail routes.
    """

    queryset = selectors.trip_queryset()
    permission_classes = [IsAuthenticated, IsTripOwner]
    filterset_class = TripFilterSet
    search_fields = ("name", "description")
    ordering_fields = ("created_at", "start_date", "name")
    ordering = ("-created_at",)

    serializer_class = TripDetailSerializer
    serializer_classes = {
        "list": TripListSerializer,
        "retrieve": TripDetailSerializer,
        "create": TripWriteSerializer,
        "update": TripWriteSerializer,
        "partial_update": TripWriteSerializer,
        "cover_photo": CoverPhotoSerializer,
    }

    #: Actions whose response nests the itinerary, so they need the deep prefetch.
    DETAIL_ACTIONS = frozenset({"retrieve", "update", "partial_update", "cover_photo"})

    def get_queryset(self):
        queryset = super().get_queryset()  # owner-scoped by the mixin
        if self.action in self.DETAIL_ACTIONS:
            return selectors.with_stop_activities(queryset)
        return queryset

    def _cost_context(self, trips):
        """
        Serializer context carrying **one** bulk cost lookup for these trips.

        Passed explicitly rather than built inside the serializer so a page of
        20 trips costs one cost query, not 20 (trap #9).
        """
        return {
            **self.get_serializer_context(),
            "cost_summaries": selectors.cost_summaries_for([trip.pk for trip in trips]),
        }

    def _detail_response(self, trip, message: str | None = None, *, respond=success):
        """The detail body every read and write action answers with."""
        data = TripDetailSerializer(trip, context=self._cost_context([trip])).data
        return respond(data=data, message=message)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "group_by",
                enum=list(selectors.GROUP_BY_CHOICES),
                description=(
                    "Adds `data.groups` — `[{key, label, count}]` over the whole "
                    "filtered set, not just this page. `results` stays flat."
                ),
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # Pagination is the DRF default and this view does not opt out, so
        # `page` is never None here.
        page = self.paginate_queryset(queryset)
        serializer = TripListSerializer(page, many=True, context=self._cost_context(page))
        response = self.get_paginated_response(serializer.data)

        # Screen 3's "Group by" control. A sibling of `results`, not a
        # replacement for it: the cards render from the flat list and the chips
        # from the counts, so asking for both must not cost two requests.
        group_by = request.query_params.get("group_by")
        if group_by in selectors.GROUP_BY_CHOICES:
            response.data["groups"] = selectors.trip_groups(queryset, group_by)
        return response

    def retrieve(self, request, *args, **kwargs):
        return self._detail_response(self.get_object())

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trip = services.create_trip(user=request.user, **serializer.validated_data)
        return self._detail_response(
            trip, message="Trip created successfully.", respond=created
        )

    def update(self, request, *args, **kwargs):
        trip = self.get_object()
        serializer = self.get_serializer(
            instance=trip, data=request.data, partial=kwargs.pop("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        trip = services.update_trip(trip, **serializer.validated_data)
        return self._detail_response(trip, message="Trip updated.")

    def destroy(self, request, *args, **kwargs):
        services.delete_trip(self.get_object())
        return no_content()

    @extend_schema(
        summary="Share or unshare this trip",
        request=None,
        responses={200: TripShareSerializer},
    )
    @action(detail=True, methods=["post", "delete"], url_path="share")
    def share(self, request, pk=None):
        """
        `POST` publishes, `DELETE` revokes. The token survives both — revoking
        and re-sharing gives back the same link, which is what somebody who
        pasted it into a chat expects.
        """
        trip = services.set_trip_public(self.get_object(), is_public=request.method == "POST")
        return success(
            data=TripShareSerializer(trip).data,
            message="Trip is now public." if trip.is_public else "Sharing revoked.",
        )

    @extend_schema(
        summary="Issue a new share token, killing existing links",
        request=None,
        responses={200: TripShareSerializer},
    )
    @action(detail=True, methods=["post"], url_path="share/regenerate")
    def share_regenerate(self, request, pk=None):
        trip = services.regenerate_share_token(self.get_object())
        return success(
            data=TripShareSerializer(trip).data,
            message="New share link issued. The old one no longer works.",
        )

    @extend_schema(
        summary="Upload a cover photo",
        request=CoverPhotoSerializer,
        responses={200: TripDetailSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="cover-photo",
        parser_classes=[MultiPartParser, FormParser],
    )
    def cover_photo(self, request, pk=None):
        """`multipart/form-data`, field `cover_photo`."""
        trip = self.get_object()
        serializer = self.get_serializer(instance=trip, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self._detail_response(trip, message="Cover photo updated.")


# ---------------------------------------------------------------------- stops


@extend_schema(tags=["trip stops"])
class TripStopListCreateView(TripScopedMixin, generics.ListCreateAPIView):
    """`GET|POST /trips/{trip_id}/stops/` — the sections of Screen 5."""

    def get_queryset(self):
        return selectors.stop_queryset(self.trip)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TripStopWriteSerializer
        return TripStopSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stop = services.create_stop(trip=self.trip, **serializer.validated_data)
        return created(
            data=TripStopSerializer(stop, context=self.get_serializer_context()).data,
            message="Stop added.",
        )


@extend_schema(tags=["trip stops"])
class TripStopDetailView(TripScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    """`GET|PATCH|DELETE /trips/{trip_id}/stops/{id}/`."""

    def get_queryset(self):
        return selectors.stop_queryset(self.trip)

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return TripStopWriteSerializer
        return TripStopSerializer

    def update(self, request, *args, **kwargs):
        stop = self.get_object()
        serializer = self.get_serializer(
            instance=stop, data=request.data, partial=kwargs.pop("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        stop = services.update_stop(stop, **serializer.validated_data)
        return success(
            data=TripStopSerializer(stop, context=self.get_serializer_context()).data,
            message="Stop updated.",
        )

    def destroy(self, request, *args, **kwargs):
        services.delete_stop(self.get_object())
        return no_content()


@extend_schema(
    tags=["trip stops"],
    summary="Reorder stops",
    request=StopReorderSerializer,
    responses={200: TripStopSerializer(many=True)},
)
class TripStopReorderView(TripScopedMixin, generics.GenericAPIView):
    """`POST /trips/{trip_id}/stops/reorder/` — drag-to-reorder, one statement."""

    serializer_class = StopReorderSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.reorder_stops(trip=self.trip, items=serializer.validated_data["items"])
        # Re-read through the selector so the response carries the joined city
        # rows rather than lazy-loading one per stop.
        stops = selectors.stop_queryset(self.trip)
        return success(
            data=TripStopSerializer(
                stops, many=True, context=self.get_serializer_context()
            ).data,
            message="Stops reordered.",
        )


# ----------------------------------------------------------- trip activities


@extend_schema(tags=["trip activities"])
class TripActivityListCreateView(StopScopedMixin, generics.ListCreateAPIView):
    """`GET|POST /trips/{trip_id}/stops/{stop_id}/activities/`."""

    def get_queryset(self):
        return selectors.stop_activity_queryset(self.stop)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TripActivityCreateSerializer
        return TripActivitySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trip_activity = services.create_trip_activity(
            trip_stop=self.stop, **serializer.validated_data
        )
        return created(
            data=TripActivitySerializer(
                trip_activity, context=self.get_serializer_context()
            ).data,
            message="Activity added.",
        )


@extend_schema(tags=["trip activities"])
class TripActivityDetailView(OwnerQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    `GET|PATCH|DELETE /trip-activities/{id}/`.

    Flat on purpose: calendar drag-and-drop moves an item between days *and*
    stops, so a nested URL would encode a parent that is about to change.
    """

    queryset = selectors.trip_activity_queryset()
    owner_field = "trip_stop__trip__user"
    permission_classes = [IsAuthenticated, IsTripOwner]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return TripActivityUpdateSerializer
        return TripActivitySerializer

    def update(self, request, *args, **kwargs):
        trip_activity = self.get_object()
        serializer = self.get_serializer(
            instance=trip_activity, data=request.data, partial=kwargs.pop("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        trip_activity = services.update_trip_activity(
            trip_activity, **serializer.validated_data
        )
        return success(
            data=TripActivitySerializer(trip_activity).data, message="Activity updated."
        )

    def destroy(self, request, *args, **kwargs):
        services.delete_trip_activity(self.get_object())
        return no_content()


@extend_schema(
    tags=["itinerary"],
    summary="Day-wise itinerary",
    parameters=[
        OpenApiParameter(
            "view",
            enum=["day", "stop"],
            description="`day` (default) returns `days`; `stop` groups them under `stops`.",
        )
    ],
    responses={200: ItinerarySerializer},
)
class TripItineraryView(TripScopedMixin, generics.GenericAPIView):
    """
    `GET /trips/{trip_id}/itinerary/` — Screen 10.

    **Not paginated.** A trip is a bounded object and the screen renders all of
    it at once; paginating would split a fortnight across two requests.
    """

    serializer_class = ItinerarySerializer
    pagination_class = None

    def get(self, request, *args, **kwargs):
        days = selectors.itinerary_for_trip(self.trip)
        summary = selectors.cost_summaries_for([self.trip.pk])[self.trip.pk]

        payload = {
            "trip": self.trip,
            "totals": {
                "activities_cost": summary["activities_cost"],
                "expenses_cost": summary["expenses_cost"],
                "grand_total": summary["grand_total"],
            },
        }
        if request.query_params.get("view") == "stop":
            payload["stops"] = selectors.group_itinerary_by_stop(days)
        else:
            payload["days"] = days

        return success(data=ItinerarySerializer(payload).data)


@extend_schema(
    tags=["trip activities"],
    summary="Reorder activities, and move them between days or stops",
    request=ActivityReorderSerializer,
    responses={200: TripActivitySerializer(many=True)},
)
class TripActivityReorderView(TripScopedMixin, generics.GenericAPIView):
    """`POST /trips/{trip_id}/activities/reorder/`."""

    serializer_class = ActivityReorderSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activities = services.reorder_trip_activities(
            trip=self.trip, items=serializer.validated_data["items"]
        )
        return success(
            data=TripActivitySerializer(activities, many=True).data,
            message="Activities reordered.",
        )


# --------------------------------------------------------------------- public


@extend_schema(tags=["public"], responses={200: PublicTripSerializer})
class PublicTripView(generics.GenericAPIView):
    """
    `GET /public/trips/{share_token}/` — the shared itinerary. **No auth.**

    A trip that is not public, or has been deleted, is a plain 404: the response
    must not distinguish "wrong token" from "that person stopped sharing".
    """

    serializer_class = PublicTripSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    pagination_class = None

    def get_object(self) -> Trip:
        return get_object_or_404(
            Trip.objects.filter(is_public=True).select_related("user"),
            share_token=self.kwargs["share_token"],
        )

    def get(self, request, *args, **kwargs):
        trip = self.get_object()
        services.record_public_view(trip)
        summary = selectors.cost_summaries_for([trip.pk])[trip.pk]

        return success(
            data=PublicTripSerializer(
                {
                    "trip": trip,
                    "owner": trip.user,
                    "description": trip.description,
                    "cover_photo": trip.cover_photo,
                    # +1 in memory: the increment above was an F() expression,
                    # so this instance still holds the pre-increment value.
                    "views_count": trip.views_count + 1,
                    "days": selectors.itinerary_for_trip(trip),
                    "totals": {
                        "activities_cost": summary["activities_cost"],
                        "expenses_cost": summary["expenses_cost"],
                        "grand_total": summary["grand_total"],
                    },
                },
                context={"request": request},
            ).data
        )


@extend_schema(
    tags=["public"],
    summary="Copy a shared trip into my account",
    request=TripCopySerializer,
    responses={201: TripDetailSerializer},
)
class PublicTripCopyView(generics.GenericAPIView):
    """
    `POST /public/trips/{share_token}/copy/` — Screen 11's "Copy Trip".

    Requires a login, unlike the page itself: the copy has to land in somebody's
    account.
    """

    serializer_class = TripCopySerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        source = get_object_or_404(
            Trip.objects.filter(is_public=True), share_token=kwargs["share_token"]
        )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        trip = services.copy_trip(
            source=source, user=request.user, **serializer.validated_data
        )
        return created(
            data=TripDetailSerializer(
                selectors.with_stop_activities(selectors.trip_queryset()).get(pk=trip.pk),
                context={
                    "request": request,
                    "cost_summaries": selectors.cost_summaries_for([trip.pk]),
                },
            ).data,
            message="Trip copied to your account.",
        )


# ---------------------------------------------------------------------- admin


class AdminTripCostMixin:
    """
    Serialize a page of trips with **one** bulk cost lookup.

    Shared by the two admin trip lists so neither of them reaches for
    `trip_cost_summary` per row, which is what turns a moderation table into a
    hundred queries.
    """

    def paginated_trips(self, queryset):
        page = self.paginate_queryset(queryset)
        serializer = AdminTripSerializer(
            page,
            many=True,
            context={
                "request": self.request,
                "cost_summaries": selectors.cost_summaries_for([trip.pk for trip in page]),
            },
        )
        return self.get_paginated_response(serializer.data)


@extend_schema(tags=["admin-trips"])
class AdminTripListView(AdminOnlyMixin, AdminTripCostMixin, generics.ListAPIView):
    """`GET /admin/trips/` — every trip on the platform."""

    serializer_class = AdminTripSerializer
    filterset_class = AdminTripFilterSet
    search_fields = ("name", "description", "user__email")
    ordering_fields = ("created_at", "start_date", "views_count")
    ordering = ("-created_at",)

    def get_queryset(self):
        return selectors.admin_trip_queryset()

    def list(self, request, *args, **kwargs):
        return self.paginated_trips(self.filter_queryset(self.get_queryset()))


@extend_schema(tags=["admin-trips"])
class AdminTripDetailView(
    AdminOnlyMixin, UnfilteredObjectMixin, generics.RetrieveDestroyAPIView
):
    """
    `GET|DELETE /admin/trips/{id}/`.

    No `PATCH`: a moderator removes a trip, they do not rewrite somebody's
    itinerary. Delete is soft, so the row stays available to analytics and can be
    restored from `/django-admin/` if it was a mistake.
    """

    serializer_class = AdminTripSerializer

    def get_queryset(self):
        return selectors.admin_trip_queryset()

    def retrieve(self, request, *args, **kwargs):
        trip = self.get_object()
        return success(
            data=AdminTripSerializer(
                trip,
                context={
                    "request": request,
                    "cost_summaries": selectors.cost_summaries_for([trip.pk]),
                },
            ).data
        )

    def destroy(self, request, *args, **kwargs):
        services.delete_trip(self.get_object())
        return no_content()


@extend_schema(tags=["admin-users"], summary="One user's trips")
class AdminUserTripListView(AdminOnlyMixin, AdminTripCostMixin, generics.ListAPIView):
    """
    `GET /admin/users/{user_id}/trips/`.

    Lives in `trips`, not `accounts`, even though the URL says `users`: it
    serves trips, and `accounts` may not import `trips` (`LAYOUT.md` §5). The URL
    prefix and the owning app are allowed to differ — `SavedDestination` does the
    same thing in reverse.
    """

    serializer_class = AdminTripSerializer
    filterset_class = AdminTripFilterSet
    ordering_fields = ("created_at", "start_date")
    ordering = ("-created_at",)

    def get_queryset(self):
        return selectors.admin_trip_queryset().filter(user_id=self.kwargs["user_id"])

    def list(self, request, *args, **kwargs):
        return self.paginated_trips(self.filter_queryset(self.get_queryset()))
