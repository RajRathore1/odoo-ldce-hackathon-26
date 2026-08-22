"""Tests for the geo seed commands and the shared city resolver.

These use synthetic cities rather than the imported GeoNames data, so they
run without the (slow, network-bound) `cities_light` import.
"""

import json
from decimal import Decimal
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from .models import Activity, City, Country
from .services import resolve_city


class ResolveCityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.colombia = Country.objects.create(
            name="Colombia", code2="CO", continent="SA"
        )
        cls.france = Country.objects.create(name="France", code2="FR", continent="EU")
        cls.usa = Country.objects.create(
            name="United States", code2="US", continent="NA"
        )

        # Accented name: name_ascii is populated to "Bogota" by the receiver.
        cls.bogota = City.objects.create(
            name="Bogotá", country=cls.colombia, population=7_674_366
        )
        cls.paris_fr = City.objects.create(
            name="Paris", country=cls.france, population=2_138_551
        )
        # Same name, different country -- the code must disambiguate.
        cls.paris_tx = City.objects.create(
            name="Paris", country=cls.usa, population=24_782
        )

    def test_resolves_plain_ascii_name(self):
        self.assertEqual(resolve_city("Paris", "FR"), self.paris_fr)

    def test_country_code_disambiguates_a_repeated_name(self):
        self.assertEqual(resolve_city("Paris", "US"), self.paris_tx)

    def test_accented_fixture_value_resolves(self):
        """to_ascii() normalises the query, so the accent is optional."""
        self.assertEqual(resolve_city("Bogotá", "CO"), self.bogota)

    def test_unaccented_fixture_value_also_resolves(self):
        self.assertEqual(resolve_city("Bogota", "CO"), self.bogota)

    def test_country_code_is_case_insensitive(self):
        self.assertEqual(resolve_city("paris", "fr"), self.paris_fr)

    def test_returns_none_when_nothing_matches(self):
        self.assertIsNone(resolve_city("Atlantis", "FR"))
        self.assertIsNone(resolve_city("Paris", "JP"))

    def test_largest_population_wins_within_one_country(self):
        small = City.objects.create(
            name="Springfield", country=self.usa, population=1_000
        )
        big = City.objects.create(
            name="Springfield", country=self.usa, population=170_000
        )
        self.assertEqual(resolve_city("Springfield", "US"), big)
        self.assertNotEqual(resolve_city("Springfield", "US"), small)

    def test_null_population_does_not_outrank_a_real_one(self):
        City.objects.create(name="Nowhere", country=self.usa, population=None)
        real = City.objects.create(name="Nowhere", country=self.usa, population=5_000)
        self.assertEqual(resolve_city("Nowhere", "US"), real)

    def test_falls_back_to_alternate_names(self):
        """GeoNames stores Zurich's asciiname as "Zuerich", so the English
        exonym only resolves via alternate_names."""
        zurich = City.objects.create(
            name="Zürich",
            country=self.france,  # country is irrelevant here, only the code
            population=415_367,
            alternate_names="Turicum,Zurich,Zurigo",
        )
        self.assertEqual(resolve_city("Zurich", "FR"), zurich)

    def test_alternate_name_matches_only_whole_tokens(self):
        """A substring match would let "York" resolve to New York."""
        City.objects.create(
            name="Nouvelle Ville",
            country=self.france,
            population=9_000_000,
            alternate_names="New York,Nueva York",
        )
        self.assertIsNone(resolve_city("York", "FR"))

    def test_alternate_name_token_matches_at_each_position(self):
        for alternates in ("Solo", "Solo,Other", "Other,Solo", "A,Solo,B"):
            with self.subTest(alternates=alternates):
                city = City.objects.create(
                    name=f"City {alternates}",
                    country=self.france,
                    population=100,
                    alternate_names=alternates,
                )
                self.assertEqual(resolve_city("Solo", "FR"), city)
                city.delete()

    def test_exact_name_ascii_wins_over_an_alternate_name(self):
        """A city actually called X outranks one merely aliased to X."""
        aliased = City.objects.create(
            name="Aliased",
            country=self.france,
            population=9_000_000,
            alternate_names="Lyon",
        )
        real = City.objects.create(name="Lyon", country=self.france, population=500_000)
        self.assertEqual(resolve_city("Lyon", "FR"), real)
        self.assertNotEqual(resolve_city("Lyon", "FR"), aliased)


class SeedCommandTestCase(TestCase):
    """Points both commands at temporary fixtures instead of the real ones."""

    @classmethod
    def setUpTestData(cls):
        cls.japan = Country.objects.create(name="Japan", code2="JP", continent="AS")
        cls.tokyo = City.objects.create(
            name="Tokyo", country=cls.japan, population=8_336_599
        )

    def run_seed(self, command, module_path, rows):
        """Run a seed command against an in-memory fixture."""
        out = StringIO()
        payload = json.dumps(rows)
        with mock.patch(f"{module_path}.FIXTURE") as fixture:
            fixture.read_text.return_value = payload
            call_command(command, stdout=out, stderr=out)
        return out.getvalue()


class SeedCityProfilesTests(SeedCommandTestCase):
    MODULE = "geo.management.commands.seed_city_profiles"

    def test_sets_curated_fields_on_a_matched_city(self):
        self.run_seed(
            "seed_city_profiles",
            self.MODULE,
            [
                {
                    "name": "Tokyo",
                    "country": "JP",
                    "cost_index": 4.0,
                    "popularity": 96,
                    "blurb": "Neon and shrines.",
                }
            ],
        )
        self.tokyo.refresh_from_db()
        self.assertEqual(self.tokyo.cost_index, Decimal("4.0"))
        self.assertEqual(self.tokyo.popularity, 96)
        self.assertEqual(self.tokyo.blurb, "Neon and shrines.")

    def test_reports_unmatched_rows_instead_of_failing(self):
        output = self.run_seed(
            "seed_city_profiles",
            self.MODULE,
            [
                {
                    "name": "Tokyo",
                    "country": "JP",
                    "cost_index": 4.0,
                    "popularity": 96,
                    "blurb": "ok",
                },
                {
                    "name": "Atlantis",
                    "country": "JP",
                    "cost_index": 1.0,
                    "popularity": 1,
                    "blurb": "nope",
                },
            ],
        )
        self.assertIn("Profiled 1 of 2", output)
        self.assertIn("Atlantis", output)
        # The good row still landed.
        self.tokyo.refresh_from_db()
        self.assertEqual(self.tokyo.popularity, 96)

    def test_is_idempotent(self):
        rows = [
            {
                "name": "Tokyo",
                "country": "JP",
                "cost_index": 4.0,
                "popularity": 96,
                "blurb": "ok",
            }
        ]
        self.run_seed("seed_city_profiles", self.MODULE, rows)
        self.run_seed("seed_city_profiles", self.MODULE, rows)
        self.tokyo.refresh_from_db()
        self.assertEqual(self.tokyo.popularity, 96)

    def test_refuses_to_run_on_an_empty_catalogue(self):
        City.objects.all().delete()
        output = self.run_seed("seed_city_profiles", self.MODULE, [])
        self.assertIn("No cities in the database", output)


class SeedActivitiesTests(SeedCommandTestCase):
    MODULE = "geo.management.commands.seed_activities"

    ROWS = [
        {
            "city": "Tokyo",
            "country": "JP",
            "name": "Tsukiji Market Breakfast",
            "category": "food",
            "cost": 25,
            "duration_minutes": 120,
            "popularity": 88,
            "description": "Very early sushi.",
        }
    ]

    def test_creates_activities(self):
        output = self.run_seed("seed_activities", self.MODULE, self.ROWS)
        self.assertIn("1 created", output)

        activity = Activity.objects.get()
        self.assertEqual(activity.city, self.tokyo)
        self.assertEqual(activity.slug, "tsukiji-market-breakfast")
        self.assertEqual(activity.cost, Decimal("25"))
        self.assertEqual(activity.category, "food")

    def test_rerun_updates_rather_than_duplicating(self):
        self.run_seed("seed_activities", self.MODULE, self.ROWS)
        changed = [{**self.ROWS[0], "cost": 30}]
        output = self.run_seed("seed_activities", self.MODULE, changed)

        self.assertIn("0 created, 1 updated", output)
        self.assertEqual(Activity.objects.count(), 1)
        self.assertEqual(Activity.objects.get().cost, Decimal("30"))

    def test_skips_and_reports_rows_whose_city_is_missing(self):
        rows = self.ROWS + [
            {
                "city": "Atlantis",
                "country": "JP",
                "name": "Underwater Tour",
                "category": "adventure",
                "cost": 10,
                "duration_minutes": 60,
            }
        ]
        output = self.run_seed("seed_activities", self.MODULE, rows)
        self.assertIn("1 skipped", output)
        self.assertIn("Underwater Tour", output)
        self.assertEqual(Activity.objects.count(), 1)

    def test_refuses_to_run_on_an_empty_catalogue(self):
        City.objects.all().delete()
        output = self.run_seed("seed_activities", self.MODULE, [])
        self.assertIn("No cities in the database", output)
