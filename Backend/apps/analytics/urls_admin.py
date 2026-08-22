"""
Admin routes for analytics. Mounted by `config/admin_urls.py` under
`/api/v1/admin/analytics/`.

⚠️ The mount point does **not** apply permissions — each view carries
`AdminOnlyMixin` itself, because DRF resolves permission classes on the view and
authentication happens inside it (trap #8).
"""

from django.urls import path

from apps.analytics.views import AnalyticsOverviewView

urlpatterns = [
    path("overview/", AnalyticsOverviewView.as_view(), name="admin-analytics-overview"),
]
