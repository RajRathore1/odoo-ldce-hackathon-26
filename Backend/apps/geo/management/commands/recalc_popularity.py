"""
Rebuild `City.popularity_score` from the trip stops that point at each city.

The counter is maintained incrementally by `trips.services.create_stop`, so this
is the repair job: run it after seeding, after a bulk delete, or any time the
"Popular destinations" list looks wrong.

    python manage.py recalc_popularity
    python manage.py recalc_popularity --city 61
"""

from django.core.management.base import BaseCommand

from apps.geo.services import recalculate_city_popularity


class Command(BaseCommand):
    help = "Recalculate City.popularity_score from live trip stops."

    def add_arguments(self, parser):
        parser.add_argument(
            "--city",
            type=int,
            default=None,
            help="Only this city id. Omit to rebuild every city.",
        )

    def handle(self, *args, **options):
        updated = recalculate_city_popularity(options["city"])
        # No emoji: a Windows console cannot encode them and the command would
        # die on its own success message (HANDOFF.md §5 #10).
        self.stdout.write(self.style.SUCCESS(f"Recalculated popularity for {updated} cities."))
