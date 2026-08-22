"""Backfill the curated fields cities-light does not provide."""

import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand

from geo.models import City
from geo.services import resolve_city

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "city_profiles.json"


class Command(BaseCommand):
    help = "Set cost_index, popularity and blurb on the curated cities."

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
        updated, unmatched = [], []

        for row in rows:
            city = resolve_city(row["name"], row["country"])
            if city is None:
                unmatched.append(f"{row['name']} ({row['country']})")
                continue

            city.cost_index = Decimal(str(row["cost_index"]))
            city.popularity = row["popularity"]
            city.blurb = row["blurb"]
            updated.append(city)

        City.objects.bulk_update(updated, ["cost_index", "popularity", "blurb"])

        self.stdout.write(
            self.style.SUCCESS(f"Profiled {len(updated)} of {len(rows)} cities.")
        )
        if unmatched:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(unmatched)} not found in the imported data "
                    f"(check the GeoNames spelling):"
                )
            )
            for name in unmatched:
                self.stdout.write(f"  - {name}")
