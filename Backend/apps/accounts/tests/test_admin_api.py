"""accounts — the admin user-management tree (task B6.1, B6.2)."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.constants import UserRole
from apps.accounts.models import User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, AdminFactory, UserFactory
from apps.trips.tests.factories import TripFactory

pytestmark = pytest.mark.django_db

LIST_URL = reverse("admin-user-list")


def detail_url(user_id) -> str:
    return reverse("admin-user-detail", args=[user_id])


def signed_in(user) -> APIClient:
    api = APIClient()
    response = api.post(
        reverse("auth-login"),
        {"email": user.email, "password": DEFAULT_PASSWORD},
        format="json",
    )
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['tokens']['access']}")
    return api


@pytest.fixture
def admin():
    return AdminFactory(email="admin@globetrotter.dev")


@pytest.fixture
def client(admin):
    return signed_in(admin)


class TestAdminUserList:
    def test_the_row_carries_the_moderation_fields(self, client, admin):
        user = UserFactory(email="riya@example.com", first_name="Riya", last_name="Sharma")
        TripFactory.create_batch(2, user=user)

        rows = {row["email"]: row for row in client.get(LIST_URL).json()["data"]["results"]}

        assert rows["riya@example.com"]["full_name"] == "Riya Sharma"
        assert rows["riya@example.com"]["role"] == UserRole.USER
        assert rows["riya@example.com"]["trips_count"] == 2
        assert rows["riya@example.com"]["is_deleted"] is False
        # Community is cut, so this is always 0 — the key stays for the UI.
        assert rows["riya@example.com"]["posts_count"] == 0

    def test_a_deleted_trip_does_not_count(self, client):
        user = UserFactory(email="riya@example.com")
        TripFactory(user=user)
        TripFactory(user=user).delete()

        rows = {row["email"]: row for row in client.get(LIST_URL).json()["data"]["results"]}

        assert rows["riya@example.com"]["trips_count"] == 1

    def test_deleted_users_are_hidden_by_default(self, client):
        UserFactory(email="gone@example.com").delete()

        emails = {row["email"] for row in client.get(LIST_URL).json()["data"]["results"]}

        assert "gone@example.com" not in emails

    def test_include_deleted_reveals_them(self, client):
        UserFactory(email="gone@example.com").delete()

        body = client.get(LIST_URL, {"include_deleted": "true"}).json()
        rows = {row["email"]: row for row in body["data"]["results"]}

        assert rows["gone@example.com"]["is_deleted"] is True

    def test_it_searches_by_email_and_name(self, client):
        UserFactory(email="riya@example.com", first_name="Riya")
        UserFactory(email="other@example.com", first_name="Sam")

        body = client.get(LIST_URL, {"search": "riya"}).json()

        assert [row["email"] for row in body["data"]["results"]] == ["riya@example.com"]

    def test_it_filters_by_role(self, client, admin):
        UserFactory(email="riya@example.com")

        body = client.get(LIST_URL, {"role": "ADMIN"}).json()

        assert [row["email"] for row in body["data"]["results"]] == [admin.email]

    def test_it_filters_by_active_state(self, client):
        UserFactory(email="off@example.com", is_active=False)

        body = client.get(LIST_URL, {"is_active": "false"}).json()

        assert [row["email"] for row in body["data"]["results"]] == ["off@example.com"]

    def test_query_count_does_not_grow_with_the_page(self, client, django_assert_num_queries):
        UserFactory.create_batch(3)
        with django_assert_num_queries(3) as captured:
            client.get(LIST_URL)

        UserFactory.create_batch(12)
        with django_assert_num_queries(len(captured.captured_queries)):
            client.get(LIST_URL)


class TestAdminUserDetail:
    def test_it_adds_the_rest_of_the_profile(self, client):
        user = UserFactory(email="riya@example.com", phone_number="+91 98250 11111")

        body = client.get(detail_url(user.pk)).json()["data"]

        assert body["phone_number"] == "+91 98250 11111"
        assert body["currency"] == "INR"
        assert body["deleted_at"] is None

    def test_accounts_cannot_be_created_here(self, client):
        """Accounts are made by registering — there is no admin create route."""
        response = client.post(LIST_URL, {"email": "new@example.com"}, format="json")

        assert response.status_code == 405


class TestAdminUserModeration:
    def test_it_can_deactivate_an_account(self, client):
        user = UserFactory(email="riya@example.com")

        response = client.patch(detail_url(user.pk), {"is_active": False}, format="json")

        assert response.status_code == 200
        assert response.json()["message"] == "User updated."
        user.refresh_from_db()
        assert user.is_active is False

    def test_deactivating_revokes_the_users_sessions(self, client):
        """
        Otherwise a suspended account keeps working until its access token
        expires, which defeats the point of suspending it.
        """
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

        user = UserFactory(email="riya@example.com")
        signed_in(user)  # mints a refresh token

        client.patch(detail_url(user.pk), {"is_active": False}, format="json")

        assert BlacklistedToken.objects.filter(token__user=user).exists()

    def test_reactivating_does_not_revoke_anything(self, client):
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

        user = UserFactory(email="riya@example.com", is_active=False)
        client.patch(detail_url(user.pk), {"is_active": True}, format="json")

        assert not BlacklistedToken.objects.filter(token__user=user).exists()

    def test_it_can_promote_and_demote(self, client):
        user = UserFactory(email="riya@example.com")

        client.patch(detail_url(user.pk), {"role": UserRole.ADMIN}, format="json")

        user.refresh_from_db()
        assert user.role == UserRole.ADMIN
        assert user.is_admin is True

    def test_it_cannot_edit_the_profile_itself(self, client):
        """Narrow on purpose: moderation, not a general-purpose user editor."""
        user = UserFactory(email="riya@example.com", first_name="Riya")

        client.patch(
            detail_url(user.pk),
            {"first_name": "Hijacked", "email": "new@example.com", "currency": "USD"},
            format="json",
        )

        user.refresh_from_db()
        assert (user.first_name, user.email, user.currency) == (
            "Riya",
            "riya@example.com",
            "INR",
        )

    def test_delete_is_soft(self, client):
        user = UserFactory(email="riya@example.com")

        response = client.delete(detail_url(user.pk))

        assert response.status_code == 204
        assert not User.objects.filter(pk=user.pk).exists()
        assert User.all_objects.filter(pk=user.pk).exists()

    def test_restore_brings_the_account_back_usable(self, client):
        """
        `delete_account` also set `is_active=False`, so a restore that only
        undeleted would hand back a row nobody can log in to.
        """
        user = UserFactory(email="riya@example.com")
        client.delete(detail_url(user.pk))

        response = client.post(reverse("admin-user-restore", args=[user.pk]))

        assert response.status_code == 200
        assert response.json()["message"] == "User restored."
        user.refresh_from_db()
        assert user.is_deleted is False
        assert user.is_active is True

    def test_a_restored_user_can_sign_in_again(self, client):
        user = UserFactory(email="riya@example.com")
        client.delete(detail_url(user.pk))
        client.post(reverse("admin-user-restore", args=[user.pk]))

        response = APIClient().post(
            reverse("auth-login"),
            {"email": user.email, "password": DEFAULT_PASSWORD},
            format="json",
        )

        assert response.status_code == 200
