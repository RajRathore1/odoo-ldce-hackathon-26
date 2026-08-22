"""
Root URL configuration.

    /django-admin/     Django's HTML admin — for fixing data by hand mid-demo
    /api/v1/admin/     admin API   -> config/admin_urls.py
    /api/v1/           user API    -> config/api_urls.py
    /api/schema/       OpenAPI schema
    /api/docs/         Swagger UI  <- the frontend team's reference
    /api/redoc/        ReDoc
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("django-admin/", admin.site.urls),
    # ⚠️ Order matters. This must come before the /api/v1/ include below, or the
    # user tree's routes swallow "admin/" as a detail lookup.
    path("api/v1/admin/", include("config.admin_urls")),
    path("api/v1/", include("config.api_urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    # Django serves uploaded avatars and cover photos in dev only.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
