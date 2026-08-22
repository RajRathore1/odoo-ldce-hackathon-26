"""
Admin routes for activities. Mounted by `config/admin_urls.py` under
`/api/v1/admin/`.

⚠️ The mount point does **not** apply permissions (trap #8) — every view here
carries `AdminOnlyMixin` itself.
"""

from rest_framework.routers import SimpleRouter

from apps.activities.views import AdminActivityCategoryViewSet, AdminActivityViewSet

router = SimpleRouter()
router.register(
    "activity-categories", AdminActivityCategoryViewSet, basename="admin-activity-category"
)
router.register("activities", AdminActivityViewSet, basename="admin-activity")

urlpatterns = router.urls
