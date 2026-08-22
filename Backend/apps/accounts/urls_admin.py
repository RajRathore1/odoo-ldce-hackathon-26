"""
Admin routes for accounts. Mounted by `config/admin_urls.py` under
`/api/v1/admin/`.

⚠️ The mount point does **not** apply permissions (trap #8) — each view carries
`AdminOnlyMixin` itself. The one exception is `auth/login/`, which cannot: you
cannot require an admin token in order to obtain one. It gates inside its
serializer instead.

`/admin/users/{id}/trips/` is **not here.** It serves trips, and `accounts` may
not import `trips` (`LAYOUT.md` §5) — it lives in `apps/trips/urls_admin.py`,
which is allowed to import both.
"""

from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.accounts.views import AdminLoginView, AdminUserViewSet

router = SimpleRouter()
router.register("users", AdminUserViewSet, basename="admin-user")

urlpatterns = [
    path("auth/login/", AdminLoginView.as_view(), name="admin-login"),
    *router.urls,
]
