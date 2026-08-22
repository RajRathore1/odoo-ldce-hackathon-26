"""
core — date helpers.

These feed the itinerary and the calendar, the two screens that must emit a row
for *every* day in a range including the empty ones. An off-by-one here is a
visible bug in the demo, so the boundaries are tested explicitly.
"""

from datetime import date

from core.utils import (
    daterange,
    days_inclusive,
    month_bounds,
    month_grid,
    shift_dates,
)


class TestDaterange:
    def test_includes_both_ends(self):
        assert daterange(date(2026, 6, 1), date(2026, 6, 3)) == [
            date(2026, 6, 1),
            date(2026, 6, 2),
            date(2026, 6, 3),
        ]

    def test_single_day_trip_is_one_day_not_zero(self):
        assert daterange(date(2026, 6, 1), date(2026, 6, 1)) == [date(2026, 6, 1)]

    def test_reversed_range_is_empty_rather_than_raising(self):
        assert daterange(date(2026, 6, 3), date(2026, 6, 1)) == []

    def test_none_is_tolerated(self):
        assert daterange(None, date(2026, 6, 1)) == []
        assert daterange(date(2026, 6, 1), None) == []

    def test_spans_a_month_boundary(self):
        span = daterange(date(2026, 6, 29), date(2026, 7, 2))
        assert span == [
            date(2026, 6, 29),
            date(2026, 6, 30),
            date(2026, 7, 1),
            date(2026, 7, 2),
        ]

    def test_spans_a_leap_day(self):
        span = daterange(date(2028, 2, 28), date(2028, 3, 1))
        assert date(2028, 2, 29) in span
        assert len(span) == 3


class TestDaysInclusive:
    def test_matches_daterange_length(self):
        start, end = date(2026, 6, 1), date(2026, 6, 14)
        assert days_inclusive(start, end) == len(daterange(start, end)) == 14

    def test_same_day_is_one(self):
        assert days_inclusive(date(2026, 6, 1), date(2026, 6, 1)) == 1

    def test_invalid_is_zero_so_division_can_guard_on_it(self):
        assert days_inclusive(date(2026, 6, 3), date(2026, 6, 1)) == 0
        assert days_inclusive(None, None) == 0


class TestMonthHelpers:
    def test_month_bounds(self):
        assert month_bounds(2026, 2) == (date(2026, 2, 1), date(2026, 2, 28))
        assert month_bounds(2028, 2) == (date(2028, 2, 1), date(2028, 2, 29))

    def test_grid_is_always_whole_weeks(self):
        for month in range(1, 13):
            grid = month_grid(2026, month)
            assert len(grid) % 7 == 0, f"month {month} is not a whole number of weeks"

    def test_grid_starts_on_monday_and_covers_the_month(self):
        grid = month_grid(2026, 8)
        assert grid[0].weekday() == 0
        assert grid[-1].weekday() == 6
        assert date(2026, 8, 1) in grid
        assert date(2026, 8, 31) in grid

    def test_grid_pads_with_neighbouring_months_not_blanks(self):
        """August 2026 starts on a Saturday, so the grid must reach into July."""
        grid = month_grid(2026, 8)
        assert grid[0] == date(2026, 7, 27)


class TestShiftDates:
    def test_shifts_forward_and_back(self):
        assert shift_dates(date(2026, 6, 1), 10) == date(2026, 6, 11)
        assert shift_dates(date(2026, 6, 11), -10) == date(2026, 6, 1)

    def test_none_passes_through(self):
        """Copy Trip rebases optional dates; None must not raise."""
        assert shift_dates(None, 10) is None
