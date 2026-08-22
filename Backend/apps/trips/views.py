"""
trips — views. Owner: Dev A.

Thin. Parse the request, call a service or selector, return a response.
No business rules and no multi-step ORM work.
"""

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.trips import selectors, services
from apps.trips.filters import TripFilterSet
from apps.trips.serializers import (
    CoverPhotoSerializer,
    TripDetailSerializer,
    TripListSerializer,
    TripWriteSerializer,
)
from core.mixins import OwnerQuerysetMixin, SerializerActionMixin
from core.permissions import IsTripOwner
from core.response import created, no_content, success


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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # Pagination is the DRF default and this view does not opt out, so
        # `page` is never None here.
        page = self.paginate_queryset(queryset)
        serializer = TripListSerializer(page, many=True, context=self._cost_context(page))
        return self.get_paginated_response(serializer.data)

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
