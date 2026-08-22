"""
User-facing routes for trips. Mounted by `config/api_urls.py`.

`SimpleRouter`, not `DefaultRouter`: we do not want the browsable API root view
it adds, and this module is mounted at the API root where that route would sit
on top of `/api/v1/`.

The nested routes are written by hand rather than pulled in with
`drf-nested-routers` — six `path()` lines against another dependency, and the
`/trip-activities/{id}/` route is flat anyway, so a nested router would only
cover half of them.
"""

from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.trips.views import (
    TripActivityDetailView,
    TripActivityListCreateView,
    TripActivityReorderView,
    TripItineraryView,
    TripStopDetailView,
    TripStopListCreateView,
    TripStopReorderView,
    TripViewSet,
)

router = SimpleRouter()
router.register("trips", TripViewSet, basename="trip")

urlpatterns = [
    *router.urls,
    # Stops. `reorder/` is listed first for readability — `<int:pk>` could not
    # have matched it anyway.
    path(
        "trips/<int:trip_id>/stops/",
        TripStopListCreateView.as_view(),
        name="trip-stop-list",
    ),
    path(
        "trips/<int:trip_id>/stops/reorder/",
        TripStopReorderView.as_view(),
        name="trip-stop-reorder",
    ),
    path(
        "trips/<int:trip_id>/stops/<int:pk>/",
        TripStopDetailView.as_view(),
        name="trip-stop-detail",
    ),
    # Trip activities: nested to create and list, flat to edit and delete.
    path(
        "trips/<int:trip_id>/stops/<int:stop_id>/activities/",
        TripActivityListCreateView.as_view(),
        name="trip-activity-list",
    ),
    path(
        "trips/<int:trip_id>/activities/reorder/",
        TripActivityReorderView.as_view(),
        name="trip-activity-reorder",
    ),
    # Itinerary — Screen 10. Not paginated; a trip is a bounded object.
    path(
        "trips/<int:trip_id>/itinerary/",
        TripItineraryView.as_view(),
        name="trip-itinerary",
    ),
    path(
        "trip-activities/<int:pk>/",
        TripActivityDetailView.as_view(),
        name="trip-activity-detail",
    ),
]
