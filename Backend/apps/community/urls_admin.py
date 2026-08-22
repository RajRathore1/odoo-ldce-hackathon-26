"""
Admin routes for community. Mounted by `config/admin_urls.py` under
`/api/v1/admin/`.

⚠️ The mount point does **not** apply permissions (trap #8) — every view here
carries `AdminOnlyMixin` itself.
"""

from django.urls import path

from apps.community.views import AdminPostDetailView, AdminPostListView

urlpatterns = [
    path("posts/", AdminPostListView.as_view(), name="admin-post-list"),
    path("posts/<int:pk>/", AdminPostDetailView.as_view(), name="admin-post-detail"),
]
