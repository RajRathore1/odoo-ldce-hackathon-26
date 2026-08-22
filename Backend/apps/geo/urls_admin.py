"""
Admin routes for geo. Mounted by `config/admin_urls.py` under `/api/v1/admin/`.

⚠️ The mount point does **not** apply permissions (trap #8) — every view here
carries `AdminOnlyMixin` itself.
"""

from rest_framework.routers import SimpleRouter

from apps.geo.views import AdminCityViewSet, AdminCountryViewSet

router = SimpleRouter()
router.register("countries", AdminCountryViewSet, basename="admin-country")
router.register("cities", AdminCityViewSet, basename="admin-city")

urlpatterns = router.urls
