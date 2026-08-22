"""geo — the admin master-data tree (task B6.4)."""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, AdminFactory
from apps.geo.models import City, Country
from apps.geo.tests.factories import CityFactory, CountryFactory

pytestmark = pytest.mark.django_db

COUNTRIES = reverse("admin-country-list")
CITIES = reverse("admin-city-list")


@pytest.fixture
def client():
    admin = AdminFactory(email="admin@globetrotter.dev")
    api = APIClient()
    response = api.post(
        reverse("auth-login"),
        {"email": admin.email, "password": DEFAULT_PASSWORD},
        format="json",
    )
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['tokens']['access']}")
    return api


class TestAdminCountryCrud:
    def test_it_creates_a_country(self, client):
        response = client.post(
            COUNTRIES,
            {
                "name": "Iceland",
                "iso2": "IS",
                "iso3": "ISL",
                "region": "Europe",
                "currency_code": "ISK",
            },
            format="json",
        )

        assert response.status_code == 201
        assert Country.objects.filter(iso2="IS").exists()

    def test_a_duplicate_iso2_is_a_field_error(self, client):
        CountryFactory(name="India", iso2="IN")

        response = client.post(COUNTRIES, {"name": "Not India", "iso2": "IN"}, format="json")

        assert response.status_code == 400
        assert "iso2" in response.json()["errors"]["fields"]

    def test_it_patches_a_country(self, client):
        country = CountryFactory(name="India", iso2="IN", region="Asia")

        response = client.patch(
            reverse("admin-country-detail", args=[country.pk]),
            {"region": "South Asia"},
            format="json",
        )

        assert response.status_code == 200
        country.refresh_from_db()
        assert country.region == "South Asia"

    def test_delete_is_soft(self, client):
        """`City.country` is PROTECT, so a hard delete of a country in use would
        be refused outright. Soft delete keeps the admin tree usable."""
        country = CountryFactory(name="India", iso2="IN")
        CityFactory(country=country)

        response = client.delete(reverse("admin-country-detail", args=[country.pk]))

        assert response.status_code == 204
        assert not Country.objects.filter(pk=country.pk).exists()
        assert Country.all_objects.filter(pk=country.pk).exists()

    def test_deleted_rows_are_hidden_but_reachable_by_id(self, client):
        country = CountryFactory(name="India", iso2="IN")
        client.delete(reverse("admin-country-detail", args=[country.pk]))

        listed = client.get(COUNTRIES).json()["data"]["results"]
        with_deleted = client.get(COUNTRIES, {"include_deleted": "true"}).json()

        assert [row["id"] for row in listed] == []
        assert [row["id"] for row in with_deleted["data"]["results"]] == [country.pk]
        # A detail route addresses one row by id — the list default must not hide it.
        assert (
            client.get(reverse("admin-country-detail", args=[country.pk])).status_code == 200
        )

    def test_is_deleted_is_read_only(self, client):
        country = CountryFactory(name="India", iso2="IN")

        client.patch(
            reverse("admin-country-detail", args=[country.pk]),
            {"is_deleted": True},
            format="json",
        )

        country.refresh_from_db()
        assert country.is_deleted is False


class TestAdminCityCrud:
    def test_it_creates_a_city(self, client):
        country = CountryFactory(name="India", iso2="IN")

        response = client.post(
            CITIES,
            {
                "country": country.pk,
                "name": "Rishikesh",
                "state": "Uttarakhand",
                "cost_index": "46.00",
                "avg_daily_cost": "2000.00",
                "currency": "INR",
            },
            format="json",
        )
        body = response.json()

        assert response.status_code == 201
        assert body["data"]["country_name"] == "India"
        assert City.objects.filter(name="Rishikesh").exists()

    def test_popularity_score_cannot_be_typed_over(self, client):
        """
        It is a counter maintained by `create_stop` and rebuilt by
        `recalc_popularity`. An admin editing it would make the popular-cities
        list disagree with the trips behind it.
        """
        city = CityFactory(popularity_score=7)

        client.patch(
            reverse("admin-city-detail", args=[city.pk]),
            {"popularity_score": 9999},
            format="json",
        )

        city.refresh_from_db()
        assert city.popularity_score == 7

    def test_it_patches_the_curated_fields(self, client):
        city = CityFactory()

        response = client.patch(
            reverse("admin-city-detail", args=[city.pk]),
            {"description": "Rewritten", "cost_index": "88.50", "is_active": False},
            format="json",
        )

        assert response.status_code == 200
        city.refresh_from_db()
        assert city.description == "Rewritten"
        assert city.cost_index == Decimal("88.50")
        assert city.is_active is False

    def test_it_filters_by_country(self, client):
        india = CountryFactory(name="India", iso2="IN")
        match = CityFactory(country=india)
        CityFactory()

        body = client.get(CITIES, {"country": india.pk}).json()

        assert [row["id"] for row in body["data"]["results"]] == [match.pk]

    def test_deactivating_a_city_hides_it_from_the_user_api(self, client):
        """The admin edit has to actually reach the user-facing search."""
        city = CityFactory(name="Bir")

        client.patch(
            reverse("admin-city-detail", args=[city.pk]),
            {"is_active": False},
            format="json",
        )

        popular = APIClient().get(reverse("city-popular")).json()["data"]
        assert [row["id"] for row in popular] == []
