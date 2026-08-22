"""
analytics — views. Owner: Dev B.

Thin. Parse the request, call a service or selector, return a response.
No business rules and no multi-step ORM work.
"""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics

from apps.analytics import selectors
from apps.analytics.constants import AnalyticsPeriod
from apps.analytics.serializers import AnalyticsOverviewSerializer
from core.mixins import AdminOnlyMixin
from core.response import success


@extend_schema(
    tags=["admin-analytics"],
    summary="KPI tiles",
    parameters=[
        OpenApiParameter(
            "period",
            enum=[choice.value for choice in AnalyticsPeriod],
            description="Window for the *_this_period figures. Defaults to 30d.",
        )
    ],
    responses={200: AnalyticsOverviewSerializer},
)
class AnalyticsOverviewView(AdminOnlyMixin, generics.GenericAPIView):
    """
    `GET /admin/analytics/overview/` — Screen 13's tile row.

    `AdminOnlyMixin` is not optional (trap #8): DRF resolves permissions per
    view, so `config/admin_urls.py` cannot gate its own subtree. Without the
    mixin this would fall back to the global `IsAuthenticated` and any logged-in
    user would be reading platform totals.

    **Not paginated** — a fixed set of tiles.
    """

    serializer_class = AnalyticsOverviewSerializer
    pagination_class = None

    def get(self, request, *args, **kwargs):
        period = selectors.resolve_period(request.query_params.get("period"))
        return success(data=AnalyticsOverviewSerializer(selectors.overview(period)).data)
