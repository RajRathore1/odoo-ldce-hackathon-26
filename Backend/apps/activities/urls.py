"""
User-facing routes for activities. Mounted by `config/api_urls.py`.
"""

from django.urls import path

from apps.activities.views import (
    ActivityCategoryListView,
    ActivityDetailView,
    ActivityListView,
    PopularActivityListView,
)

urlpatterns = [
    path(
        "activity-categories/",
        ActivityCategoryListView.as_view(),
        name="activity-category-list",
    ),
    path("activities/", ActivityListView.as_view(), name="activity-list"),
    path("activities/popular/", PopularActivityListView.as_view(), name="activity-popular"),
    path("activities/<int:pk>/", ActivityDetailView.as_view(), name="activity-detail"),
]
