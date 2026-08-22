"""activities — the admin catalog tree (task B6.5)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, AdminFactory
from apps.activities.constants import ActivityType
from apps.activities.models import Activity, ActivityCategory
from apps.activities.tests.factories import ActivityCategoryFactory, ActivityFactory
from apps.geo.tests.factories import CityFactory
from apps.trips.services import create_trip_activity
from apps.trips.tests.factories import TripFactory, TripStopFactory

pytestmark = pytest.mark.django_db

TODAY = date.today()
CATEGORIES = reverse("admin-activity-category-list")
ACTIVITIES = reverse("admin-activity-list")


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


class TestAdminCategoryCrud:
    def test_it_creates_a_category(self, client):
        response = client.post(
            CATEGORIES,
            {"name": "Wellness", "slug": "wellness", "icon": "lotus"},
            format="json",
        )

        assert response.status_code == 201
        assert ActivityCategory.objects.filter(slug="wellness").exists()

    def test_a_duplicate_slug_is_a_field_error(self, client):
        ActivityCategoryFactory(name="Adventure", slug="adventure")

        response = client.post(
            CATEGORIES, {"name": "Other", "slug": "adventure"}, format="json"
        )

        assert response.status_code == 400
        assert "slug" in response.json()["errors"]["fields"]

    def test_delete_is_soft_so_activities_are_not_orphaned(self, client):
        """`Activity.category` is SET_NULL — a hard delete would quietly null it."""
        category = ActivityCategoryFactory()
        activity = ActivityFactory(category=category)

        response = client.delete(reverse("admin-activity-category-detail", args=[category.pk]))

        assert response.status_code == 204
        activity.refresh_from_db()
        assert activity.category_id == category.pk


class TestAdminActivityCrud:
    def test_it_creates_an_activity(self, client):
        city = CityFactory(name="Bir")
        category = ActivityCategoryFactory()

        response = client.post(
            ACTIVITIES,
            {
                "city": city.pk,
                "category": category.pk,
                "name": "Night sky walk",
                "activity_type": ActivityType.NATURE,
                "cost": "800.00",
                "currency": "INR",
                "duration_minutes": 120,
            },
            format="json",
        )
        body = response.json()

        assert response.status_code == 201
        assert body["data"]["city_name"] == "Bir"
        assert Activity.objects.filter(name="Night sky walk").exists()

    def test_an_unknown_activity_type_is_rejected(self, client):
        response = client.post(
            ACTIVITIES,
            {"name": "Nope", "activity_type": "TELEPORTING", "cost": "1.00"},
            format="json",
        )

        assert response.status_code == 400

    def test_editing_the_catalog_price_does_not_touch_saved_trips(self, client):
        """
        Trap #5, from the admin side. A curator fixing a price must not rewrite
        budgets users have already seen — the snapshot on `TripActivity` is the
        whole point.
        """
        activity = ActivityFactory(cost=Decimal("2500.00"))
        trip = TripFactory(
            start_date=TODAY + timedelta(days=10), end_date=TODAY + timedelta(days=14)
        )
        stop = TripStopFactory(
            trip=trip, city=activity.city, start_date=trip.start_date, end_date=trip.end_date
        )
        saved = create_trip_activity(
            trip_stop=stop, activity=activity, custom_title="", day_date=trip.start_date
        )

        response = client.patch(
            reverse("admin-activity-detail", args=[activity.pk]),
            {"cost": "9999.00"},
            format="json",
        )

        assert response.status_code == 200
        activity.refresh_from_db()
        saved.refresh_from_db()
        assert activity.cost == Decimal("9999.00")
        assert saved.cost == Decimal("2500.00")

    def test_popularity_score_is_read_only(self, client):
        activity = ActivityFactory(popularity_score=12)

        client.patch(
            reverse("admin-activity-detail", args=[activity.pk]),
            {"popularity_score": 9999},
            format="json",
        )

        activity.refresh_from_db()
        assert activity.popularity_score == 12

    def test_delete_is_soft(self, client):
        activity = ActivityFactory()

        response = client.delete(reverse("admin-activity-detail", args=[activity.pk]))

        assert response.status_code == 204
        assert not Activity.objects.filter(pk=activity.pk).exists()
        assert Activity.all_objects.filter(pk=activity.pk).exists()

    def test_a_deleted_activity_is_hidden_from_the_user_catalog(self, client):
        activity = ActivityFactory()
        client.delete(reverse("admin-activity-detail", args=[activity.pk]))

        listed = client.get(ACTIVITIES).json()["data"]["results"]
        user_facing = client.get(reverse("activity-list")).json()["data"]

        assert [row["id"] for row in listed] == []
        assert user_facing["pagination"]["count"] == 0
        # Still addressable by id, so it can be inspected or restored.
        assert (
            client.get(reverse("admin-activity-detail", args=[activity.pk])).status_code == 200
        )

    def test_it_filters_by_city_and_type(self, client):
        city = CityFactory()
        match = ActivityFactory(city=city, activity_type=ActivityType.FOOD)
        ActivityFactory(city=city, activity_type=ActivityType.SHOPPING)
        ActivityFactory()

        body = client.get(ACTIVITIES, {"city": city.pk, "activity_type": "FOOD"}).json()

        assert [row["id"] for row in body["data"]["results"]] == [match.pk]

    def test_query_count_does_not_grow_with_the_page(self, client, django_assert_num_queries):
        ActivityFactory.create_batch(3)
        with django_assert_num_queries(3) as captured:
            client.get(ACTIVITIES)

        ActivityFactory.create_batch(12)
        with django_assert_num_queries(len(captured.captured_queries)):
            client.get(ACTIVITIES)
