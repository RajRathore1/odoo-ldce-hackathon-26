"""Small helpers with no knowledge of any app."""

from __future__ import annotations

import calendar
from datetime import date, timedelta

from django.conf import settings


def daterange(start: date, end: date) -> list[date]:
    """
    Every date from `start` to `end`, **inclusive of both ends**.

    Inclusive because a trip from the 1st to the 3rd is three days, not two, and
    because the itinerary must emit a row for every day in range — including the
    empty ones. Returns `[]` if `end` precedes `start`.

        >>> daterange(date(2026, 6, 1), date(2026, 6, 3))
        [date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3)]
    """
    if start is None or end is None or end < start:
        return []
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def days_inclusive(start: date, end: date) -> int:
    """Length of a date range in days, both ends counted. 0 if invalid."""
    if start is None or end is None or end < start:
        return 0
    return (end - start).days + 1


def month_bounds(year: int, month: int) -> tuple[date, date]:
    """First and last date of a calendar month."""
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def month_grid(year: int, month: int, week_starts_monday: bool = True) -> list[date]:
    """
    A month padded out to whole weeks, for the calendar view.

    The frontend renders a fixed 7-column grid, so it needs the trailing days of
    the previous month and the leading days of the next one rather than blanks
    it has to compute itself.
    """
    first, last = month_bounds(year, month)
    offset = first.weekday() if week_starts_monday else (first.weekday() + 1) % 7
    grid_start = first - timedelta(days=offset)

    trailing = 6 - (last.weekday() if week_starts_monday else (last.weekday() + 1) % 7)
    grid_end = last + timedelta(days=trailing)

    return daterange(grid_start, grid_end)


def shift_dates(value: date | None, days: int) -> date | None:
    """Move a date by `days`, tolerating `None`. Used when copying a trip."""
    return None if value is None else value + timedelta(days=days)


def build_share_url(share_token) -> str:
    """
    Public link for a shared trip.

    Points at the **frontend**, not this API — it is a link a human opens, and
    the frontend calls `/api/v1/public/trips/{token}/` to fill the page.
    """
    return f"{settings.FRONTEND_BASE_URL}/trips/shared/{share_token}"
