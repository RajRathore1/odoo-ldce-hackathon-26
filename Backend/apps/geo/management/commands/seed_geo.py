"""
Load the country and city catalog from `fixtures/`.

Idempotent: `core.utils.seed_upsert` matches on the natural key, so re-running
after an edit to the JSON refreshes the rows instead of duplicating them — and
it copes with `Country` having *two* unique fields, `iso2` and `name`.
`popularity_score` is deliberately **not** in the defaults: it is earned by trip
stops and must survive a re-seed.

    python manage.py seed_geo

⚠️ The fixtures are opened with an explicit `encoding="utf-8"`. Without it
Python picks the Windows ANSI codepage and `Île-de-France` lands in the database
as `ÃŽle-de-France` — which is exactly what happens if you `loaddata` these
files on Windows without `PYTHONUTF8=1`.
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.geo.models import City, Country
from core.utils import seed_upsert

FIXTURES = Path(settings.BASE_DIR) / "fixtures"


def load(name: str) -> list[dict]:
    path = FIXTURES / name
    if not path.exists():
        raise CommandError(f"Missing fixture: {path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def image_for(kind: str, slug: str) -> str:
    """
    A real, stable placeholder image.

    picsum.photos serves a deterministic photo per seed, so every city has a
    picture in the demo without us shipping binaries or hot-linking a CDN that
    might 404 in front of judges.
    """
    return f"https://picsum.photos/seed/{kind}-{slug}/800/600"


class Command(BaseCommand):
    help = "Seed countries and cities from fixtures/countries.json and cities.json."

    @transaction.atomic
    def handle(self, *args, **options):
        countries = {}
        for row in load("countries.json"):
            country, _ = seed_upsert(
                Country,
                # Both `iso2` and `name` are unique, so either could already be
                # taken by the row we are about to write.
                [{"iso2": row["iso2"]}, {"name": row["name"]}],
                {
                    "iso3": row.get("iso3", ""),
                    "region": row.get("region", ""),
                    "currency_code": row.get("currency_code", ""),
                    "flag_emoji": row.get("flag_emoji", ""),
                    "is_active": True,
                },
            )
            countries[row["iso2"]] = country

        created = updated = 0
        for row in load("cities.json"):
            country = countries.get(row["country_iso2"])
            if country is None:
                raise CommandError(
                    f"City {row['name']} references unknown country "
                    f"{row['country_iso2']}. Add it to countries.json first."
                )

            slug = row["name"].lower().replace(" ", "-")
            _, was_created = seed_upsert(
                City,
                # The one unique key: (country, name, state).
                [
                    {
                        "country": country,
                        "name": row["name"],
                        "state": row.get("state", ""),
                    }
                ],
                {
                    "latitude": row.get("lat"),
                    "longitude": row.get("lng"),
                    "timezone": row.get("timezone", ""),
                    "cost_index": row.get("cost_index", 0),
                    "avg_daily_cost": row.get("avg_daily_cost", 0),
                    "currency": row.get("currency", ""),
                    "description": row.get("description", ""),
                    "image_url": row.get("image_url") or image_for("city", slug),
                    "is_active": True,
                },
            )
            created += was_created
            updated += not was_created

        # No emoji in the output: a Windows console cannot encode the flags we
        # just seeded, and the command would die on its own success message.
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(countries)} countries; "
                f"{created} cities created, {updated} updated."
            )
        )
