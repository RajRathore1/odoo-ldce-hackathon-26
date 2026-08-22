"""
Admin routes for trips. Mounted by `config/admin_urls.py` under `/api/v1/admin/`.

⚠️ The mount point does **not** apply permissions (trap #8) — every view here
carries `AdminOnlyMixin` itself.

`users/<id>/trips/` is served from this module rather than `accounts` because it
returns trips, and `accounts` may not import `trips` (`LAYOUT.md` §5).
"""

from django.urls import path

from apps.trips.views import (
    AdminTripDetailView,
    AdminTripListView,
    AdminUserTripListView,
)

urlpatterns = [
    path("trips/", AdminTripListView.as_view(), name="admin-trip-list"),
    path("trips/<int:pk>/", AdminTripDetailView.as_view(), name="admin-trip-detail"),
    path(
        "users/<int:user_id>/trips/",
        AdminUserTripListView.as_view(),
        name="admin-user-trips",
    ),
]
