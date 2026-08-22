"""
User-facing routes for dashboard. Mounted by `config/api_urls.py`.
"""

from django.urls import path

from apps.dashboard.views import DashboardView

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
