"""Load the bundled activity catalogue."""

import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from geo.models import Activity, City
from geo.services import resolve_city

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "activities.json"


class Command(BaseCommand):
    help = "Seed the Activity catalogue from geo/fixtures/activities.json."

    def handle(self, *args, **options):
        if not City.objects.exists():
            self.stderr.write(
                self.style.ERROR(
                    "No cities in the database. Run `manage.py cities_light` "
                    "or load the committed fixture first."
                )
            )
            return

        rows = json.loads(FIXTURE.read_text(encoding="utf-8"))
        created = updated = 0
        unmatched = []
        # One lookup per distinct city rather than per activity row.
        cache = {}

        for row in rows:
            key = (row["city"], row["country"])
            if key not in cache:
                cache[key] = resolve_city(*key)
            city = cache[key]

            if city is None:
                unmatched.append(f"{row['name']} -> {row['city']} ({row['country']})")
                continue

            _, was_created = Activity.objects.update_or_create(
                city=city,
                slug=slugify(row["name"])[:220],
                defaults={
                    "name": row["name"],
                    "category": row["category"],
                    "description": row.get("description", ""),
                    "cost": Decimal(str(row["cost"])),
                    "duration_minutes": row["duration_minutes"],
                    "popularity": row.get("popularity", 0),
                    "is_active": True,
                },
            )
            created += was_created
            updated += not was_created

        self.stdout.write(
            self.style.SUCCESS(
                f"Activities: {created} created, {updated} updated, "
                f"{len(unmatched)} skipped."
            )
        )
        if unmatched:
            self.stdout.write(self.style.WARNING("Skipped (city not found):"))
            for line in unmatched:
                self.stdout.write(f"  - {line}")
