"""
User-facing routes for trips. Mounted by `config/api_urls.py`.

`SimpleRouter`, not `DefaultRouter`: we do not want the browsable API root view
it adds, and this module is mounted at the API root where that route would sit
on top of `/api/v1/`.
"""

from rest_framework.routers import SimpleRouter

from apps.trips.views import TripViewSet

router = SimpleRouter()
router.register("trips", TripViewSet, basename="trip")

urlpatterns = router.urls
