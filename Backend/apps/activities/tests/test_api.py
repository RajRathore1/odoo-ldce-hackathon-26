"""activities — Status codes, envelope shape, permissions."""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, UserFactory
from apps.activities.constants import ActivityType
from apps.activities.tests.factories import ActivityCategoryFactory, ActivityFactory
from apps.geo.tests.factories import CityFactory, CountryFactory

pytestmark = pytest.mark.django_db

LIST_URL = reverse("activity-list")
POPULAR_URL = reverse("activity-popular")
CATEGORIES_URL = reverse("activity-category-list")


@pytest.fixture
def client():
    user = UserFactory(email="riya@example.com")
    api = APIClient()
    response = api.post(
        reverse("auth-login"),
        {"email": user.email, "password": DEFAULT_PASSWORD},
        format="json",
    )
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['tokens']['access']}")
    return api


class TestActivityCategoryList:
    def test_it_requires_authentication(self):
        assert APIClient().get(CATEGORIES_URL).status_code == 401

    def test_it_is_not_paginated(self, client):
        ActivityCategoryFactory(name="Adventure", slug="adventure", icon="mountain")

        body = client.get(CATEGORIES_URL).json()

        assert isinstance(body["data"], list)
        assert body["data"][0]["slug"] == "adventure"
        assert body["data"][0]["icon"] == "mountain"

    def test_an_inactive_category_is_left_out(self, client):
        ActivityCategoryFactory(is_active=False)
        assert client.get(CATEGORIES_URL).json()["data"] == []


class TestActivityList:
    def test_it_requires_authentication(self):
        assert APIClient().get(LIST_URL).status_code == 401

    def test_the_row_shape(self, client):
        india = CountryFactory(name="India", iso2="IN")
        city = CityFactory(country=india, name="Bir")
        category = ActivityCategoryFactory(name="Adventure", slug="adventure", icon="mountain")
        activity = ActivityFactory(
            city=city,
            category=category,
            name="Paragliding at Bir Billing",
            description="20-minute tandem flight.",
            activity_type=ActivityType.ADVENTURE,
            cost=Decimal("2500.00"),
            duration_minutes=90,
            rating=Decimal("4.6"),
            popularity_score=340,
        )

        row = client.get(LIST_URL).json()["data"]["results"][0]

        assert row["id"] == activity.pk
        assert row["name"] == "Paragliding at Bir Billing"
        assert row["activity_type"] == ActivityType.ADVENTURE
        assert row["category"] == {
            "id": category.pk,
            "name": "Adventure",
            "slug": "adventure",
            "icon": "mountain",
        }
        assert row["city"]["name"] == "Bir"
        assert row["city"]["country_name"] == "India"
        assert row["cost"] == "2500.00"
        assert row["duration_minutes"] == 90
        assert row["rating"] == "4.6"
        assert row["popularity_score"] == 340

    def test_page_size_is_fifty(self, client):
        ActivityFactory()
        assert client.get(LIST_URL).json()["data"]["pagination"]["page_size"] == 50

    def test_default_order_is_most_popular_first(self, client):
        quiet = ActivityFactory(popularity_score=1)
        busy = ActivityFactory(popularity_score=99)

        body = client.get(LIST_URL).json()

        assert [row["id"] for row in body["data"]["results"]] == [busy.pk, quiet.pk]

    def test_a_deleted_activity_is_hidden(self, client):
        ActivityFactory().delete()
        assert client.get(LIST_URL).json()["data"]["pagination"]["count"] == 0

    def test_query_count_does_not_grow_with_the_page(self, client, django_assert_num_queries):
        """Trap #9 — every row nests a category and a city, and the city a country."""
        ActivityFactory.create_batch(3)
        with django_assert_num_queries(3) as captured:
            client.get(LIST_URL)

        ActivityFactory.create_batch(12)
        with django_assert_num_queries(len(captured.captured_queries)):
            client.get(LIST_URL)


class TestActivityListFilters:
    def test_search_covers_name_and_description(self, client):
        match = ActivityFactory(name="Paragliding", description="tandem flight")
        ActivityFactory(name="Museum tour", description="guided")

        body = client.get(LIST_URL, {"search": "tandem"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [match.pk]

    def test_filters_by_city(self, client):
        city = CityFactory()
        match = ActivityFactory(city=city)
        ActivityFactory()

        body = client.get(LIST_URL, {"city": city.pk}).json()

        assert [row["id"] for row in body["data"]["results"]] == [match.pk]

    def test_filters_by_country(self, client):
        india = CountryFactory(name="India", iso2="IN")
        match = ActivityFactory(city=CityFactory(country=india))
        ActivityFactory()

        body = client.get(LIST_URL, {"country": india.pk}).json()

        assert [row["id"] for row in body["data"]["results"]] == [match.pk]

    def test_filters_by_several_types_at_once(self, client):
        """Screen 8 filters with multi-select chips, not a single dropdown."""
        adventure = ActivityFactory(activity_type=ActivityType.ADVENTURE)
        food = ActivityFactory(activity_type=ActivityType.FOOD)
        ActivityFactory(activity_type=ActivityType.SHOPPING)

        body = client.get(LIST_URL, {"activity_type": "ADVENTURE,FOOD"}).json()

        assert {row["id"] for row in body["data"]["results"]} == {adventure.pk, food.pk}

    def test_filters_by_several_categories_at_once(self, client):
        first, second = ActivityCategoryFactory(), ActivityCategoryFactory()
        one = ActivityFactory(category=first)
        two = ActivityFactory(category=second)
        ActivityFactory(category=ActivityCategoryFactory())

        body = client.get(LIST_URL, {"category": f"{first.pk},{second.pk}"}).json()

        assert {row["id"] for row in body["data"]["results"]} == {one.pk, two.pk}

    def test_filters_by_cost_bounds(self, client):
        cheap = ActivityFactory(cost=Decimal("300.00"))
        ActivityFactory(cost=Decimal("5000.00"))

        body = client.get(LIST_URL, {"max_cost": "1000"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [cheap.pk]

    def test_filters_by_duration_bounds(self, client):
        short = ActivityFactory(duration_minutes=30)
        ActivityFactory(duration_minutes=480)

        body = client.get(LIST_URL, {"max_duration": 60}).json()

        assert [row["id"] for row in body["data"]["results"]] == [short.pk]

    def test_orders_by_cost(self, client):
        dear = ActivityFactory(cost=Decimal("5000.00"))
        cheap = ActivityFactory(cost=Decimal("300.00"))

        body = client.get(LIST_URL, {"ordering": "cost"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [cheap.pk, dear.pk]

    def test_orders_by_rating_descending(self, client):
        good = ActivityFactory(rating=Decimal("4.8"))
        poor = ActivityFactory(rating=Decimal("2.1"))

        body = client.get(LIST_URL, {"ordering": "-rating"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [good.pk, poor.pk]


class TestActivityDetail:
    def test_it_returns_one_activity(self, client):
        activity = ActivityFactory(name="Paragliding")

        body = client.get(reverse("activity-detail", args=[activity.pk])).json()

        assert body["data"]["name"] == "Paragliding"

    def test_a_deleted_activity_is_a_404(self, client):
        activity = ActivityFactory()
        activity.delete()

        assert client.get(reverse("activity-detail", args=[activity.pk])).status_code == 404


class TestPopularActivities:
    def test_it_is_not_paginated_and_most_popular_first(self, client):
        quiet = ActivityFactory(popularity_score=1)
        busy = ActivityFactory(popularity_score=99)

        body = client.get(POPULAR_URL).json()

        assert [row["id"] for row in body["data"]] == [busy.pk, quiet.pk]

    def test_it_can_be_scoped_to_a_city(self, client):
        city = CityFactory()
        match = ActivityFactory(city=city)
        ActivityFactory()

        body = client.get(POPULAR_URL, {"city": city.pk}).json()

        assert [row["id"] for row in body["data"]] == [match.pk]

    def test_it_defaults_to_ten(self, client):
        ActivityFactory.create_batch(12)
        assert len(client.get(POPULAR_URL).json()["data"]) == 10

    def test_an_absurd_limit_is_capped(self, client):
        ActivityFactory.create_batch(3)
        assert len(client.get(POPULAR_URL, {"limit": 100000}).json()["data"]) == 3

    def test_a_nonsense_city_is_ignored_rather_than_a_500(self, client):
        ActivityFactory()
        assert client.get(POPULAR_URL, {"city": "paris"}).status_code == 200

    def test_an_inactive_activity_is_left_out(self, client):
        ActivityFactory(is_active=False)
        assert client.get(POPULAR_URL).json()["data"] == []
