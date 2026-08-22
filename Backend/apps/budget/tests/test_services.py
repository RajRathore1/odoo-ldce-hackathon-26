"""budget — the one cost formula. If these drift, four screens disagree."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.budget.constants import AlertType, ExpenseCategory
from apps.budget.services import (
    bulk_trip_cost_summary,
    trip_budget_breakdown,
    trip_cost_summary,
)
from apps.budget.tests.factories import ExpenseFactory
from apps.trips.tests.factories import TripActivityFactory, TripFactory, TripStopFactory

pytestmark = pytest.mark.django_db

TODAY = date.today()


@pytest.fixture
def trip():
    """A ten-day trip with a 50 000 budget — the numbers in `API.md` §7.6."""
    return TripFactory(
        start_date=TODAY + timedelta(days=30),
        end_date=TODAY + timedelta(days=39),
        total_budget=Decimal("50000.00"),
    )


@pytest.fixture
def stop(trip):
    return TripStopFactory(
        trip=trip,
        order=1,
        start_date=trip.start_date,
        end_date=trip.start_date + timedelta(days=4),
        budget=Decimal("18000.00"),
    )


class TestTripCostSummary:
    def test_a_trip_with_nothing_on_it_is_all_zeros(self, trip):
        summary = trip_cost_summary(trip)

        assert summary["activities_cost"] == Decimal("0.00")
        assert summary["expenses_cost"] == Decimal("0.00")
        assert summary["grand_total"] == Decimal("0.00")
        assert summary["avg_per_day"] == Decimal("0.00")
        assert summary["remaining"] == Decimal("50000.00")
        assert summary["is_over_budget"] is False

    def test_it_adds_activities_and_expenses(self, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("2500.00"))
        ExpenseFactory(trip=trip, amount=Decimal("14000.00"))

        summary = trip_cost_summary(trip)

        assert summary["activities_cost"] == Decimal("2500.00")
        assert summary["expenses_cost"] == Decimal("14000.00")
        assert summary["grand_total"] == Decimal("16500.00")

    def test_remaining_is_null_when_no_budget_was_ever_set(self, trip, stop):
        """ "Nothing left" and "you never said" are different answers."""
        trip.total_budget = None
        trip.save(update_fields=["total_budget"])
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("500.00"))

        summary = trip_cost_summary(trip)

        assert summary["remaining"] is None
        assert summary["is_over_budget"] is False

    def test_over_budget(self, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("60000.00"))

        summary = trip_cost_summary(trip)

        assert summary["is_over_budget"] is True
        assert summary["remaining"] == Decimal("-10000.00")

    def test_spending_exactly_the_budget_is_not_over(self, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("50000.00"))

        summary = trip_cost_summary(trip)

        assert summary["is_over_budget"] is False
        assert summary["remaining"] == Decimal("0.00")

    def test_a_single_day_trip_divides_by_one(self):
        """The classic off-by-one: one day is one day, not zero."""
        trip = TripFactory(start_date=TODAY, end_date=TODAY, total_budget=Decimal("1000.00"))
        stop = TripStopFactory(trip=trip, start_date=TODAY, end_date=TODAY)
        TripActivityFactory(trip_stop=stop, day_date=TODAY, cost=Decimal("400.00"))

        summary = trip_cost_summary(trip)

        assert summary["avg_per_day"] == Decimal("400.00")

    def test_avg_per_day_spreads_over_the_whole_trip(self, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("1000.00"))

        assert trip_cost_summary(trip)["avg_per_day"] == Decimal("100.00")

    def test_a_deleted_stops_activities_stop_counting(self, trip, stop):
        """Trap #2: soft delete does not cascade, so the filter has to be explicit."""
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("2500.00"))
        stop.delete()

        assert trip_cost_summary(trip)["activities_cost"] == Decimal("0.00")

    def test_a_deleted_expense_stops_counting(self, trip):
        ExpenseFactory(trip=trip, amount=Decimal("900.00")).delete()

        assert trip_cost_summary(trip)["expenses_cost"] == Decimal("0.00")

    def test_another_trips_money_is_not_counted(self, trip, stop):
        other = TripFactory()
        other_stop = TripStopFactory(
            trip=other, start_date=other.start_date, end_date=other.end_date
        )
        TripActivityFactory(
            trip_stop=other_stop, day_date=other.start_date, cost=Decimal("9999.00")
        )
        ExpenseFactory(trip=other, amount=Decimal("9999.00"))

        assert trip_cost_summary(trip)["grand_total"] == Decimal("0.00")


class TestBulkTripCostSummary:
    def test_it_matches_the_single_trip_version(self, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("2500.00"))
        ExpenseFactory(trip=trip, amount=Decimal("1400.00"))

        assert bulk_trip_cost_summary([trip.pk])[trip.pk] == trip_cost_summary(trip)

    def test_it_keys_every_trip_separately(self, trip, stop):
        second = TripFactory(total_budget=Decimal("100.00"))
        second_stop = TripStopFactory(
            trip=second, start_date=second.start_date, end_date=second.end_date
        )
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("300.00"))
        TripActivityFactory(
            trip_stop=second_stop, day_date=second.start_date, cost=Decimal("700.00")
        )

        summaries = bulk_trip_cost_summary([trip.pk, second.pk])

        assert summaries[trip.pk]["grand_total"] == Decimal("300.00")
        assert summaries[second.pk]["grand_total"] == Decimal("700.00")
        assert summaries[second.pk]["is_over_budget"] is True

    def test_an_empty_list_costs_no_queries(self, django_assert_num_queries):
        with django_assert_num_queries(0):
            assert bulk_trip_cost_summary([]) == {}

    def test_it_is_three_queries_whatever_the_page_size(self, django_assert_num_queries):
        """Trap #9 — this is the function that keeps the trip list flat."""
        trips = TripFactory.create_batch(2)
        with django_assert_num_queries(3):
            bulk_trip_cost_summary([trip.pk for trip in trips])

        more = TripFactory.create_batch(20)
        with django_assert_num_queries(3):
            bulk_trip_cost_summary([trip.pk for trip in trips + more])


class TestBudgetBreakdown:
    def test_activities_and_activity_expenses_land_in_one_bucket(self, trip, stop):
        """
        Trap #5, the one that matters most: the `ACTIVITY` bucket is
        `SUM(TripActivity.cost)` **plus** `Expense(category=ACTIVITY)` — added
        once, here, and never double-counted.
        """
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("2000.00"))
        ExpenseFactory(trip=trip, category=ExpenseCategory.ACTIVITY, amount=Decimal("500.00"))

        breakdown = trip_budget_breakdown(trip)
        activity_bucket = next(
            bucket
            for bucket in breakdown["breakdown"]
            if bucket["category"] == ExpenseCategory.ACTIVITY
        )

        assert activity_bucket["amount"] == Decimal("2500.00")
        # And the bucket total still equals the trip total — no double count.
        assert sum(bucket["amount"] for bucket in breakdown["breakdown"]) == Decimal("2500.00")
        assert breakdown["grand_total"] == Decimal("2500.00")

    def test_buckets_sum_to_the_grand_total(self, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("2000.00"))
        ExpenseFactory(trip=trip, category=ExpenseCategory.STAY, amount=Decimal("14000.00"))
        ExpenseFactory(trip=trip, category=ExpenseCategory.MEALS, amount=Decimal("4800.00"))
        ExpenseFactory(
            trip=trip, category=ExpenseCategory.TRANSPORT, amount=Decimal("12000.00")
        )

        breakdown = trip_budget_breakdown(trip)

        assert (
            sum(bucket["amount"] for bucket in breakdown["breakdown"])
            == breakdown["grand_total"]
        )

    def test_percentages_are_precomputed_and_add_up(self, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("2500.00"))
        ExpenseFactory(trip=trip, category=ExpenseCategory.STAY, amount=Decimal("7500.00"))

        breakdown = trip_budget_breakdown(trip)

        assert {bucket["percentage"] for bucket in breakdown["breakdown"]} == {25.0, 75.0}

    def test_empty_buckets_are_omitted(self, trip, stop):
        ExpenseFactory(trip=trip, category=ExpenseCategory.STAY, amount=Decimal("100.00"))

        categories = {
            bucket["category"] for bucket in trip_budget_breakdown(trip)["breakdown"]
        }

        assert categories == {ExpenseCategory.STAY}

    def test_a_zero_cost_trip_has_no_buckets_and_no_division(self, trip):
        breakdown = trip_budget_breakdown(trip)

        assert breakdown["breakdown"] == []
        assert breakdown["grand_total"] == Decimal("0.00")

    def test_by_stop_counts_its_activities_and_its_expenses(self, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("1000.00"))
        ExpenseFactory(trip=trip, trip_stop=stop, amount=Decimal("600.00"))
        # Filed against the trip rather than the stop — trip total, not stop total.
        ExpenseFactory(trip=trip, trip_stop=None, amount=Decimal("9000.00"))

        row = trip_budget_breakdown(trip)["by_stop"][0]

        assert row["stop_id"] == stop.pk
        assert row["spent"] == Decimal("1600.00")
        assert row["budget"] == Decimal("18000.00")
        assert row["is_over_budget"] is False

    def test_a_stop_over_its_own_budget_is_flagged(self, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("20000.00"))

        assert trip_budget_breakdown(trip)["by_stop"][0]["is_over_budget"] is True

    def test_by_day_covers_every_date_in_the_range(self, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("500.00"))

        by_day = trip_budget_breakdown(trip)["by_day"]

        assert len(by_day) == trip.duration_days == 10
        assert by_day[0]["amount"] == Decimal("500.00")
        assert by_day[1]["amount"] == Decimal("0.00")

    def test_an_expense_with_no_day_stays_out_of_by_day_but_in_the_total(self, trip):
        ExpenseFactory(trip=trip, amount=Decimal("8000.00"), incurred_on=None)

        breakdown = trip_budget_breakdown(trip)

        assert all(day["amount"] == Decimal("0.00") for day in breakdown["by_day"])
        assert breakdown["grand_total"] == Decimal("8000.00")

    def test_an_expensive_day_raises_an_alert(self, trip, stop):
        """Daily allowance is 50 000 / 10 = 5 000; 6 200 is 24% over."""
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("6200.00"))

        alerts = trip_budget_breakdown(trip)["alerts"]

        assert [alert["type"] for alert in alerts] == [AlertType.OVERBUDGET_DAY]
        assert alerts[0]["date"] == stop.start_date
        assert "24%" in alerts[0]["message"]

    def test_a_day_barely_over_the_allowance_is_not_worth_an_alert(self, trip, stop):
        """5 200 is 4% over 5 000 — inside the tolerance, so no noise."""
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("5200.00"))

        breakdown = trip_budget_breakdown(trip)

        assert breakdown["alerts"] == []
        # Still flagged on the chart, just not shouted about.
        assert breakdown["by_day"][0]["is_over_budget"] is True

    def test_an_over_budget_trip_is_alerted_first(self, trip, stop):
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("60000.00"))

        alerts = trip_budget_breakdown(trip)["alerts"]

        assert alerts[0]["type"] == AlertType.OVERBUDGET_TRIP
        assert alerts[0]["date"] is None
        assert "10000.00" in alerts[0]["message"]

    def test_no_budget_means_no_alerts_at_all(self, trip, stop):
        trip.total_budget = None
        trip.save(update_fields=["total_budget"])
        TripActivityFactory(trip_stop=stop, day_date=stop.start_date, cost=Decimal("99000.00"))

        breakdown = trip_budget_breakdown(trip)

        assert breakdown["alerts"] == []
        assert all(day["is_over_budget"] is False for day in breakdown["by_day"])
        assert breakdown["remaining"] is None
