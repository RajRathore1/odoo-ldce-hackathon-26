"""
Create the demo account and **three trips in three different statuses**.

    python manage.py seed_demo

    demo@globetrotter.dev / Demo@1234

Screen 6 has Ongoing / Upcoming / Completed tabs. Two empty tabs read as a bug
in front of judges, so this seeds one trip per tab — with stops, activities and
expenses on each, so the itinerary and the budget screens have something to draw.

Safe to re-run: the demo user's existing trips are **hard**-deleted first, so
repeated runs neither pile up soft-deleted rows nor double the budget.

The dates are relative to today, so the "ongoing" trip is still ongoing next
week — a fixed date would have gone stale before the demo.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.activities.models import Activity
from apps.geo.models import City
from apps.trips import services
from apps.trips.constants import TripStatus
from apps.trips.models import Trip

DEMO_EMAIL = "demo@globetrotter.dev"
DEMO_PASSWORD = "Demo@1234"

#: `(name, description, day offset of start, length in days, budget, cities)`.
#: Offsets are relative to today, so the statuses stay true whenever this runs.
PLANS = (
    (
        "Himachal Winter",
        "Paragliding at Bir, then Manali and the Parvati valley.",
        -3,
        10,
        Decimal("50000.00"),
        ("Bir", "Manali", "Kasol"),
    ),
    (
        "Kerala Backwaters",
        "Fort Kochi, a houseboat night, and tea country.",
        30,
        9,
        Decimal("65000.00"),
        ("Kochi", "Alappuzha", "Munnar"),
    ),
    (
        "Rajasthan Loop",
        "Jaipur, Udaipur and Jodhpur by road.",
        -55,
        12,
        Decimal("80000.00"),
        ("Jaipur", "Udaipur", "Jodhpur"),
    ),
)

#: One expense per category per trip, as a share of the trip budget.
EXPENSES = (
    ("TRANSPORT", "Flights and intercity transfers", Decimal("0.28")),
    ("STAY", "Hotels and guesthouses", Decimal("0.30")),
    ("MEALS", "Food and drink", Decimal("0.12")),
    ("SHOPPING", "Souvenirs", Decimal("0.05")),
)


class Command(BaseCommand):
    help = "Create the demo user and three trips, one per Screen 6 tab."

    @transaction.atomic
    def handle(self, *args, **options):
        # Deferred, and only here: `trips → budget` is not a legal module-level
        # import (LAYOUT.md §5). Same call-time pattern the trip list uses.
        from apps.budget.models import Expense

        user = self._demo_user()
        today = timezone.localdate()

        # `hard_delete()`, not `delete()`: `SoftDeleteQuerySet.delete` *marks*
        # rows, so a plain delete here would leave last run's trips behind as
        # soft-deleted rows — piling up on every re-run and skewing the admin
        # analytics that deliberately count deleted rows. These rows are
        # disposable by definition, so they go for real, cascading to their
        # stops, activities and expenses.
        Trip.all_objects.filter(user=user).hard_delete()

        for name, description, offset, length, budget, city_names in PLANS:
            cities = self._cities(city_names)
            start = today + timedelta(days=offset)
            trip = services.create_trip(
                user=user,
                name=name,
                description=description,
                start_date=start,
                end_date=start + timedelta(days=length - 1),
                total_budget=budget,
                currency="INR",
            )
            self._add_stops_and_activities(trip, cities, length)
            self._add_expenses(trip, Expense, budget)

            self.stdout.write(f"  {trip.name}: {trip.status}, {trip.duration_days} days")

        counts = {
            status: Trip.objects.filter(user=user, status=status).count()
            for status in (TripStatus.ONGOING, TripStatus.PLANNED, TripStatus.COMPLETED)
        }
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo user {DEMO_EMAIL} / {DEMO_PASSWORD} — "
                f"ongoing {counts[TripStatus.ONGOING]}, "
                f"upcoming {counts[TripStatus.PLANNED]}, "
                f"completed {counts[TripStatus.COMPLETED]}."
            )
        )

    # ------------------------------------------------------------------ pieces

    def _demo_user(self):
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            email=DEMO_EMAIL,
            defaults={
                "first_name": "Demo",
                "last_name": "Traveller",
                "currency": "INR",
                "is_email_verified": True,
            },
        )
        # Reset every run, so a changed password in a previous demo does not
        # leave the documented credentials wrong.
        user.set_password(DEMO_PASSWORD)
        user.is_active = True
        user.save()
        if created:
            self.stdout.write(f"Created {DEMO_EMAIL}")
        return user

    def _cities(self, names: tuple[str, ...]) -> list[City]:
        cities = []
        for name in names:
            city = City.objects.filter(name=name).first()
            if city is None:
                raise CommandError(f"No city named {name}. Run `manage.py seed_geo` first.")
            cities.append(city)
        return cities

    def _add_stops_and_activities(self, trip: Trip, cities: list[City], length: int) -> None:
        """
        Split the trip evenly between its cities, then hang two activities off
        the first two days of each stop.

        Goes through `services` rather than `objects.create` on purpose: that is
        what assigns `order`, snapshots the activity cost and bumps the
        popularity counters — so the seeded data is identical to data a user
        would produce, and `/cities/popular/` is not all zeros.
        """
        per_stop = max(length // len(cities), 1)

        for index, city in enumerate(cities):
            start = trip.start_date + timedelta(days=index * per_stop)
            end = min(start + timedelta(days=per_stop - 1), trip.end_date)
            if start > trip.end_date:
                break

            stop = services.create_stop(
                trip=trip,
                city=city,
                start_date=start,
                end_date=end,
                budget=(trip.total_budget / len(cities)).quantize(Decimal("0.01")),
            )

            catalog = list(
                Activity.objects.filter(city=city, is_active=True).order_by("-rating", "name")[
                    :2
                ]
            )
            for day_offset, activity in enumerate(catalog):
                day = stop.start_date + timedelta(days=day_offset)
                if day > stop.end_date:
                    break
                services.create_trip_activity(
                    trip_stop=stop,
                    activity=activity,
                    custom_title="",
                    day_date=day,
                )

    def _add_expenses(self, trip: Trip, expense_model, budget: Decimal) -> None:
        for category, title, share in EXPENSES:
            expense_model.objects.create(
                trip=trip,
                category=category,
                title=title,
                amount=(budget * share).quantize(Decimal("0.01")),
                currency=trip.currency,
                incurred_on=trip.start_date,
                is_estimated=True,
            )
