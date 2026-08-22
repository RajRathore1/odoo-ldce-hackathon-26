"""geo — Status codes, envelope shape, permissions."""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, UserFactory
from apps.activities.tests.factories import ActivityFactory
from apps.geo.models import SavedDestination
from apps.geo.tests.factories import CityFactory, CountryFactory

pytestmark = pytest.mark.django_db

CITIES_URL = reverse("city-list")
POPULAR_URL = reverse("city-popular")
COUNTRIES_URL = reverse("country-list")
SAVED_URL = reverse("saved-destination-list")


@pytest.fixture
def user():
    return UserFactory(email="riya@example.com")


@pytest.fixture
def client(user):
    api = APIClient()
    response = api.post(
        reverse("auth-login"),
        {"email": user.email, "password": DEFAULT_PASSWORD},
        format="json",
    )
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['tokens']['access']}")
    return api


class TestCountryList:
    def test_it_is_open_to_anonymous_callers(self):
        """
        Registration accepts a `country` id, so the dropdown has to be fillable
        before the caller has a token. A list of countries is not private.
        """
        CountryFactory(name="India", iso2="IN")

        response = APIClient().get(COUNTRIES_URL)

        assert response.status_code == 200
        assert response.json()["data"]["pagination"]["count"] == 1

    def test_it_lists_countries_by_name(self, client):
        CountryFactory(name="India", iso2="IN", region="Asia")
        CountryFactory(name="France", iso2="FR", region="Europe")

        body = client.get(COUNTRIES_URL).json()

        assert [row["name"] for row in body["data"]["results"]] == ["France", "India"]
        assert body["data"]["pagination"]["page_size"] == 50

    def test_it_filters_by_region(self, client):
        CountryFactory(name="India", iso2="IN", region="Asia")
        CountryFactory(name="France", iso2="FR", region="Europe")

        body = client.get(COUNTRIES_URL, {"region": "asia"}).json()

        assert [row["name"] for row in body["data"]["results"]] == ["India"]

    def test_it_searches_by_name_and_code(self, client):
        CountryFactory(name="India", iso2="IN")
        CountryFactory(name="France", iso2="FR")

        body = client.get(COUNTRIES_URL, {"search": "fr"}).json()

        assert [row["name"] for row in body["data"]["results"]] == ["France"]


class TestCityList:
    def test_it_is_open_to_anonymous_callers(self):
        """Same reason as `/countries/`: registration accepts a `city` id."""
        CityFactory(name="Bir")

        response = APIClient().get(CITIES_URL)

        assert response.status_code == 200
        assert response.json()["data"]["results"][0]["name"] == "Bir"

    def test_is_saved_is_false_for_an_anonymous_caller(self):
        """No user to compare against, so the `Exists()` annotation is skipped."""
        CityFactory()

        row = APIClient().get(CITIES_URL).json()["data"]["results"][0]

        assert row["is_saved"] is False

    def test_the_row_shape(self, client):
        india = CountryFactory(name="India", iso2="IN", region="Asia", flag_emoji="IN")
        city = CityFactory(
            country=india,
            name="Ahmedabad",
            state="Gujarat",
            cost_index=Decimal("62.50"),
            avg_daily_cost=Decimal("2400.00"),
            popularity_score=17,
        )
        ActivityFactory.create_batch(3, city=city)

        row = client.get(CITIES_URL).json()["data"]["results"][0]

        assert row["id"] == city.pk
        assert row["name"] == "Ahmedabad"
        assert row["state"] == "Gujarat"
        assert row["country"] == {
            "id": india.pk,
            "name": "India",
            "iso2": "IN",
            "flag_emoji": "IN",
        }
        assert row["region"] == "Asia"
        assert row["cost_index"] == "62.50"
        assert row["avg_daily_cost"] == "2400.00"
        assert row["popularity_score"] == 17
        assert row["activities_count"] == 3
        assert row["is_saved"] is False

    def test_page_size_is_fifty(self, client):
        CityFactory()
        assert client.get(CITIES_URL).json()["data"]["pagination"]["page_size"] == 50

    def test_default_order_is_most_popular_first(self, client):
        quiet = CityFactory(name="Quiet", popularity_score=1)
        busy = CityFactory(name="Busy", popularity_score=99)

        body = client.get(CITIES_URL).json()

        assert [row["id"] for row in body["data"]["results"]] == [busy.pk, quiet.pk]

    def test_inactive_and_deleted_activities_are_not_counted(self, client):
        city = CityFactory()
        ActivityFactory(city=city)
        ActivityFactory(city=city, is_active=False)
        ActivityFactory(city=city).delete()

        row = client.get(CITIES_URL).json()["data"]["results"][0]

        assert row["activities_count"] == 1

    def test_is_saved_reflects_this_users_bookmarks(self, client, user):
        saved = CityFactory(name="Saved")
        CityFactory(name="Unsaved")
        SavedDestination.objects.create(user=user, city=saved)

        rows = {
            row["name"]: row["is_saved"]
            for row in client.get(CITIES_URL).json()["data"]["results"]
        }

        assert rows == {"Saved": True, "Unsaved": False}

    def test_somebody_elses_bookmark_does_not_show_as_mine(self, client):
        city = CityFactory()
        SavedDestination.objects.create(user=UserFactory(), city=city)

        assert client.get(CITIES_URL).json()["data"]["results"][0]["is_saved"] is False

    def test_query_count_does_not_grow_with_the_page(self, client, django_assert_num_queries):
        """Trap #9 — the annotations must not become per-row queries."""
        CityFactory.create_batch(3)
        with django_assert_num_queries(3) as captured:
            client.get(CITIES_URL)

        CityFactory.create_batch(12)
        with django_assert_num_queries(len(captured.captured_queries)):
            client.get(CITIES_URL)


class TestCityListFilters:
    def test_search_covers_name_state_and_country(self, client):
        india = CountryFactory(name="India", iso2="IN")
        match = CityFactory(country=india, name="Ahmedabad", state="Gujarat")
        CityFactory(name="Paris")

        for term in ("ahmed", "gujarat", "india"):
            body = client.get(CITIES_URL, {"search": term}).json()
            assert [row["id"] for row in body["data"]["results"]] == [match.pk], term

    def test_filters_by_country(self, client):
        india = CountryFactory(name="India", iso2="IN")
        match = CityFactory(country=india)
        CityFactory()

        body = client.get(CITIES_URL, {"country": india.pk}).json()

        assert [row["id"] for row in body["data"]["results"]] == [match.pk]

    def test_filters_by_region_case_insensitively(self, client):
        match = CityFactory(country=CountryFactory(iso2="IN", region="Asia"))
        CityFactory(country=CountryFactory(iso2="FR", region="Europe"))

        body = client.get(CITIES_URL, {"region": "asia"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [match.pk]

    def test_filters_by_cost_index_bounds(self, client):
        cheap = CityFactory(cost_index=Decimal("40.00"))
        CityFactory(cost_index=Decimal("150.00"))

        body = client.get(CITIES_URL, {"max_cost_index": "100"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [cheap.pk]

    def test_orders_by_cost_index(self, client):
        dear = CityFactory(cost_index=Decimal("150.00"))
        cheap = CityFactory(cost_index=Decimal("40.00"))

        body = client.get(CITIES_URL, {"ordering": "cost_index"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [cheap.pk, dear.pk]


class TestCityDetail:
    def test_it_adds_the_map_fields_and_top_activities(self, client):
        city = CityFactory(description="Manchester of India", timezone="Asia/Kolkata")
        top = ActivityFactory(city=city, popularity_score=50)
        ActivityFactory(city=city, popularity_score=1)

        body = client.get(reverse("city-detail", args=[city.pk])).json()

        assert body["data"]["description"] == "Manchester of India"
        assert body["data"]["timezone"] == "Asia/Kolkata"
        assert body["data"]["top_activities"][0]["id"] == top.pk
        assert len(body["data"]["top_activities"]) == 2

    def test_it_returns_at_most_ten_activities(self, client):
        city = CityFactory()
        ActivityFactory.create_batch(12, city=city)

        body = client.get(reverse("city-detail", args=[city.pk])).json()

        assert len(body["data"]["top_activities"]) == 10

    def test_an_inactive_activity_is_left_out(self, client):
        city = CityFactory()
        ActivityFactory(city=city, is_active=False)

        body = client.get(reverse("city-detail", args=[city.pk])).json()

        assert body["data"]["top_activities"] == []

    def test_a_deleted_city_is_a_404(self, client):
        city = CityFactory()
        city.delete()

        assert client.get(reverse("city-detail", args=[city.pk])).status_code == 404


class TestPopularCities:
    def test_it_is_not_paginated(self, client):
        CityFactory()

        body = client.get(POPULAR_URL).json()

        assert isinstance(body["data"], list)

    def test_it_returns_the_most_popular_first(self, client):
        quiet = CityFactory(popularity_score=1)
        busy = CityFactory(popularity_score=99)

        body = client.get(POPULAR_URL).json()

        assert [row["id"] for row in body["data"]] == [busy.pk, quiet.pk]

    def test_it_defaults_to_ten(self, client):
        CityFactory.create_batch(12)
        assert len(client.get(POPULAR_URL).json()["data"]) == 10

    def test_limit_is_honoured(self, client):
        CityFactory.create_batch(5)
        assert len(client.get(POPULAR_URL, {"limit": 2}).json()["data"]) == 2

    def test_an_absurd_limit_is_capped(self, client):
        """`?limit=100000` must not turn a dashboard tile into a table scan."""
        CityFactory.create_batch(3)
        assert len(client.get(POPULAR_URL, {"limit": 100000}).json()["data"]) == 3

    def test_nonsense_limit_falls_back_to_the_default(self, client):
        CityFactory.create_batch(3)
        assert len(client.get(POPULAR_URL, {"limit": "lots"}).json()["data"]) == 3

    def test_an_inactive_city_is_left_out(self, client):
        CityFactory(is_active=False)
        assert client.get(POPULAR_URL).json()["data"] == []


class TestSavedDestinations:
    def test_it_saves_a_city(self, client, user):
        city = CityFactory(name="Bir")

        response = client.post(
            SAVED_URL, {"city": city.pk, "note": "paragliding"}, format="json"
        )
        body = response.json()

        assert response.status_code == 201
        assert body["message"] == "Destination saved."
        assert body["data"]["city"]["name"] == "Bir"
        assert body["data"]["note"] == "paragliding"
        assert SavedDestination.objects.filter(user=user, city=city).exists()

    def test_saving_the_same_city_twice_is_a_conflict(self, client, user):
        city = CityFactory()
        client.post(SAVED_URL, {"city": city.pk}, format="json")

        response = client.post(SAVED_URL, {"city": city.pk}, format="json")

        assert response.status_code == 409
        assert SavedDestination.objects.filter(user=user, city=city).count() == 1

    def test_it_lists_only_my_bookmarks(self, client, user):
        mine = SavedDestination.objects.create(user=user, city=CityFactory())
        SavedDestination.objects.create(user=UserFactory(), city=CityFactory())

        body = client.get(SAVED_URL).json()

        assert [row["id"] for row in body["data"]["results"]] == [mine.pk]

    def test_delete_removes_it(self, client, user):
        saved = SavedDestination.objects.create(user=user, city=CityFactory())

        response = client.delete(reverse("saved-destination-detail", args=[saved.pk]))

        assert response.status_code == 204
        assert not SavedDestination.objects.filter(pk=saved.pk).exists()

    def test_a_removed_city_can_be_saved_again(self, client, user):
        """The unique constraint is scoped to live rows for exactly this reason."""
        city = CityFactory()
        first = client.post(SAVED_URL, {"city": city.pk}, format="json").json()["data"]["id"]
        client.delete(reverse("saved-destination-detail", args=[first]))

        assert client.post(SAVED_URL, {"city": city.pk}, format="json").status_code == 201

    def test_cannot_delete_somebody_elses_bookmark(self, client):
        theirs = SavedDestination.objects.create(user=UserFactory(), city=CityFactory())

        response = client.delete(reverse("saved-destination-detail", args=[theirs.pk]))

        assert response.status_code == 404
        assert SavedDestination.objects.filter(pk=theirs.pk).exists()

    def test_an_unknown_city_is_a_field_error(self, client):
        response = client.post(SAVED_URL, {"city": 999999}, format="json")

        assert response.status_code == 400
        assert "city" in response.json()["errors"]["fields"]
