"""
Load the activity catalog: categories, the hand-written signature activities,
and a generated baseline so **every city has something to show**.

    python manage.py seed_activities

Why generate. `fixtures/activities.json` holds the activities worth writing by
hand — the paragliding at Bir, the sunrise Taj. Hand-writing four more for every
one of ~70 cities would be a thousand lines of near-identical JSON, so the
baseline is derived from templates instead, priced off the city's own
`avg_daily_cost` so a Zurich walking tour is not 800 rupees. Screen 8 has to
return results for whichever city a judge searches; an empty city reads as a
broken API.

Idempotent, like `seed_geo`: `seed_upsert` matches on (city, name), and on
either of `ActivityCategory`'s two unique fields. `popularity_score` stays out
of the defaults so it survives a re-seed.
"""

import json
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.activities.models import Activity, ActivityCategory
from apps.geo.models import City
from core.utils import seed_upsert

FIXTURES = Path(settings.BASE_DIR) / "fixtures"

#: One per city, always. `(category slug, activity_type, name, description,
#: share of a day's budget, minutes)`.
BASELINE = (
    (
        "sightseeing",
        "SIGHTSEEING",
        "{city} half-day highlights tour",
        "The short list, with a local guide and transport between stops.",
        Decimal("0.35"),
        240,
    ),
    (
        "food",
        "FOOD",
        "{city} street-food walk",
        "Four or five stops on foot, eating where people queue.",
        Decimal("0.25"),
        150,
    ),
    (
        "culture",
        "CULTURE",
        "{city} museum and old quarter walk",
        "The city's main collection, then the streets around it.",
        Decimal("0.20"),
        180,
    ),
    (
        "nature",
        "NATURE",
        "{city} viewpoint and park walk",
        "Green space and the best view of the skyline, at your own pace.",
        Decimal("0.15"),
        150,
    ),
    (
        "shopping",
        "SHOPPING",
        "{city} market browse",
        "The main market — go with a list or leave with a rug.",
        Decimal("0.18"),
        120,
    ),
    (
        "relax",
        "RELAX",
        "Free afternoon in {city}",
        "Deliberately unscheduled. Coffee, a bench, no itinerary.",
        Decimal("0.10"),
        180,
    ),
)


def load(name: str) -> list[dict]:
    path = FIXTURES / name
    if not path.exists():
        raise CommandError(f"Missing fixture: {path}")
    # Explicit UTF-8 — see the note in seed_geo.
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def image_for(slug: str) -> str:
    return f"https://picsum.photos/seed/activity-{slug}/800/600"


def stable_rating(seed: int) -> Decimal:
    """
    A plausible, **stable** rating.

    Not `random`: a re-seed must not shuffle every rating in the catalog, and
    `hash()` is salted per process so it cannot be used either.
    """
    return Decimal("3.9") + Decimal(seed % 10) / 10


class Command(BaseCommand):
    help = "Seed activity categories and activities (curated + generated baseline)."

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {}
        for row in load("activity_categories.json"):
            category, _ = seed_upsert(
                ActivityCategory,
                # `slug` and `name` are both unique — a database seeded from
                # dev_seed.json may already hold this name under another slug.
                [{"slug": row["slug"]}, {"name": row["name"]}],
                {
                    "icon": row.get("icon", ""),
                    "description": row.get("description", ""),
                    "is_active": True,
                },
            )
            categories[row["slug"]] = category

        cities = list(City.objects.all())
        if not cities:
            raise CommandError("No cities. Run `manage.py seed_geo` first.")

        # Two dictionaries would be one too many, but these are different
        # things: the curated rows name their city, while the baseline has to
        # visit **every** city. Keying the baseline by name would silently skip
        # one of any two cities that share a name — a real risk, since `Paris`
        # and `Springfield` exist in more than one country.
        by_name: dict[str, City] = {}
        for city in cities:
            by_name.setdefault(city.name, city)

        curated = self._seed_curated(categories, by_name)
        generated = self._seed_baseline(categories, cities)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(categories)} categories, "
                f"{curated} curated and {generated} baseline activities "
                f"across {len(cities)} cities."
            )
        )

    def _seed_curated(self, categories: dict, cities: dict) -> int:
        count = 0
        for row in load("activities.json"):
            city = cities.get(row["city_name"])
            if city is None:
                self.stderr.write(
                    f"Skipping '{row['name']}': no city named {row['city_name']}."
                )
                continue

            slug = row["name"].lower().replace(" ", "-")[:60]
            seed_upsert(
                Activity,
                [{"city": city, "name": row["name"]}],
                {
                    "category": categories.get(row.get("category_slug", "")),
                    "description": row.get("description", ""),
                    "activity_type": row["activity_type"],
                    "cost": Decimal(str(row.get("cost", 0))),
                    # The city's currency, not the fixture's — a trip inherits
                    # one currency and the budget never converts.
                    "currency": city.currency or "INR",
                    "duration_minutes": row.get("duration_minutes", 60),
                    "rating": Decimal(str(row.get("rating", 4.2))),
                    "image_url": row.get("image_url") or image_for(slug),
                    "is_active": True,
                },
            )
            count += 1
        return count

    def _seed_baseline(self, categories: dict, cities: list) -> int:
        count = 0
        for city in cities:
            for index, template in enumerate(BASELINE):
                slug, activity_type, name_pattern, description, share, minutes = template
                name = name_pattern.format(city=city.name)
                cost = (city.avg_daily_cost or Decimal("0")) * share

                seed_upsert(
                    Activity,
                    [{"city": city, "name": name}],
                    {
                        "category": categories.get(slug),
                        "description": description,
                        "activity_type": activity_type,
                        "cost": cost.quantize(Decimal("1")),
                        "currency": city.currency or "INR",
                        "duration_minutes": minutes,
                        "rating": stable_rating(city.pk + index),
                        "image_url": image_for(f"{city.pk}-{index}"),
                        "is_active": True,
                    },
                )
                count += 1
        return count
