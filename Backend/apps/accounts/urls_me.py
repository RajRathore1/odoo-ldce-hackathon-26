"""
Routes for `/users/me/**`. Separate from `urls.py` because `/auth/**`
and `/users/me/**` are different prefixes owned by the same app.

`/users/me/saved-destinations/` is **not** here — that model lives in `geo`
(see `docs/MODELS.md` §4) and Dev B serves it from `apps/geo/urls.py`. Same
prefix, different app; both includes are already wired in `config/api_urls.py`.
"""

from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("users/me/", views.MeView.as_view(), name="me"),
    path("users/me/avatar/", views.AvatarView.as_view(), name="me-avatar"),
    path("users/me/stats/", views.MeStatsView.as_view(), name="me-stats"),
]
