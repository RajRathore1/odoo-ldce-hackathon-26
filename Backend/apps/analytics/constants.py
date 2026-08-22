"""
analytics — constants. Owner: Dev B.

`TextChoices` classes, enums and magic numbers. Import these into
`models.py` rather than declaring choices inline.
"""

from django.db import models


class AnalyticsPeriod(models.TextChoices):
    """The `?period=` window every analytics endpoint accepts."""

    WEEK = "7d", "Last 7 days"
    MONTH = "30d", "Last 30 days"
    QUARTER = "90d", "Last 90 days"
    ALL = "all", "All time"


#: Window length in days. `all` has none — it means "do not filter by date".
PERIOD_DAYS = {
    AnalyticsPeriod.WEEK: 7,
    AnalyticsPeriod.MONTH: 30,
    AnalyticsPeriod.QUARTER: 90,
    AnalyticsPeriod.ALL: None,
}

DEFAULT_PERIOD = AnalyticsPeriod.MONTH
