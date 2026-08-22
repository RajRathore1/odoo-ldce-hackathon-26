"""
Admin API, mounted at `/api/v1/admin/`. Consumed by `Admin_Panel/`.

A separate tree from the user API on purpose: different field exposure,
different permission class, and — during the build — two developers touching
different files even inside the same app.

⚠️ **Permissions are not enforced here.** DRF resolves permission classes per
view, and a JWT identity is not available to middleware (authentication happens
inside the view, after middleware has run), so there is no way to gate a URL
subtree from this file. Every view below must inherit
`core.mixins.AdminOnlyMixin` — a view that forgets it falls back to the global
`IsAuthenticated` default, which means any logged-in user reaches it.
Task B6.7 sweeps this whole tree checking for exactly that.
"""

from django.urls import include, path

urlpatterns = [
    # /users/**, /users/<id>/trips/
    path("", include("apps.accounts.urls_admin")),
    # /countries/, /cities/ — full CRUD
    path("", include("apps.geo.urls_admin")),
    # /activity-categories/, /activities/ — full CRUD
    path("", include("apps.activities.urls_admin")),
    # /trips/ — moderation
    path("", include("apps.trips.urls_admin")),
    # /posts/, /comments/ — moderation (P2)
    path("", include("apps.community.urls_admin")),
    # /analytics/**
    path("analytics/", include("apps.analytics.urls_admin")),
]
