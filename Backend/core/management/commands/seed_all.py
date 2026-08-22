"""
Run every seed command, in dependency order.

    python manage.py seed_all

Lives in `core` because it imports nothing — `call_command` resolves the others
by name at runtime, so this file does not give `core` a dependency on any app,
which the layering forbids (`LAYOUT.md` §5).

Safe to re-run: every command underneath it is idempotent. From nothing to a
demo-ready database:

    rm db.sqlite3 db.sqlite3-wal db.sqlite3-shm
    python manage.py migrate && python manage.py seed_all
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand

#: Order matters: activities resolve cities by name, and the demo trips need
#: both a city catalog and an activity catalog to point at.
SEEDS = ("seed_geo", "seed_activities", "seed_demo")


class Command(BaseCommand):
    help = "Seed countries, cities, activities and the demo account."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-demo",
            action="store_true",
            help="Catalog only — no demo user or trips.",
        )

    def handle(self, *args, **options):
        for name in SEEDS:
            if name == "seed_demo" and options["skip_demo"]:
                continue
            self.stdout.write(self.style.MIGRATE_HEADING(f"== {name}"))
            call_command(name)

        # After seeding, the popularity counters only reflect the demo trips'
        # stops. Rebuilding makes `/cities/popular/` honest rather than
        # dependent on whatever order the demo happened to create things in.
        self.stdout.write(self.style.MIGRATE_HEADING("== recalc_popularity"))
        call_command("recalc_popularity")

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
