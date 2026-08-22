from rest_framework.routers import DefaultRouter

from .views import ActivityViewSet, CityViewSet

router = DefaultRouter()
router.register("cities", CityViewSet, basename="city")
router.register("activities", ActivityViewSet, basename="activity")

urlpatterns = router.urls
