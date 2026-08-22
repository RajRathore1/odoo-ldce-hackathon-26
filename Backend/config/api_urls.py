"""
User-facing API, mounted at `/api/v1/`.

**Every include an app will ever need is already here.** They resolve to empty
`urlpatterns` until the routes are written, which is the point: `config/` holds
`INSTALLED_APPS` and both URL trees, so it is exactly the file two developers
would conflict on. Wiring it once during A0 means neither of us edits it again.

Adding an endpoint = adding a `path()` to the app's own `urls.py`.
"""

from django.urls import include, path

urlpatterns = [
    # accounts — split across two prefixes owned by the same app
    path("auth/", include("apps.accounts.urls")),  # /auth/**
    path("", include("apps.accounts.urls_me")),  # /users/me/**
    # geo — /cities/, /countries/, /users/me/saved-destinations/
    path("", include("apps.geo.urls")),
    # activities — /activities/, /activity-categories/
    path("", include("apps.activities.urls")),
    # trips — /trips/**, /trip-activities/**, /public/trips/**
    path("", include("apps.trips.urls")),
    # budget — /trips/<id>/expenses/**, /trips/<id>/budget/
    path("", include("apps.budget.urls")),
    # dashboard — /dashboard/. Its own app so it never collides with trips.
    path("", include("apps.dashboard.urls")),
    # community (P2)
    path("community/", include("apps.community.urls")),
]
