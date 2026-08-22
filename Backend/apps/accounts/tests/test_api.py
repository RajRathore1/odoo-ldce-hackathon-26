"""accounts — status codes, envelope shape, permissions."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import PasswordResetToken, User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db

NEW_PASSWORD = "An0ther-Str0ng!Pass"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user():
    return UserFactory(email="riya@example.com")


@pytest.fixture
def auth_client(client, user):
    response = client.post(
        reverse("auth-login"),
        {"email": user.email, "password": DEFAULT_PASSWORD},
        format="json",
    )
    tokens = response.data["data"]["tokens"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    client.refresh_token = tokens["refresh"]
    return client


# ------------------------------------------------------------------- register

class TestRegister:
    url = reverse("auth-register")

    def payload(self, **overrides):
        data = {
            "email": "new@example.com",
            "password": NEW_PASSWORD,
            "confirm_password": NEW_PASSWORD,
            "first_name": "Riya",
            "last_name": "Sharma",
        }
        return {**data, **overrides}

    def test_creates_account_and_returns_tokens(self, client):
        response = client.post(self.url, self.payload(), format="json")

        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["message"] == "Account created successfully."
        assert body["data"]["user"]["email"] == "new@example.com"
        assert body["data"]["tokens"]["access"]
        assert body["data"]["tokens"]["refresh"]

    def test_password_is_hashed_not_stored_raw(self, client):
        client.post(self.url, self.payload(), format="json")
        created = User.objects.get(email="new@example.com")
        assert created.password != NEW_PASSWORD
        assert created.check_password(NEW_PASSWORD)

    def test_password_is_never_echoed_back(self, client):
        response = client.post(self.url, self.payload(), format="json")
        assert "password" not in str(response.json())

    def test_mismatched_confirmation_is_rejected(self, client):
        response = client.post(
            self.url, self.payload(confirm_password="something-else"), format="json"
        )
        assert response.status_code == 400
        assert "confirm_password" in response.json()["errors"]["fields"]

    def test_weak_password_is_rejected_by_django_validators(self, client):
        """Proves AUTH_PASSWORD_VALIDATORS are actually reached."""
        response = client.post(
            self.url, self.payload(password="1234", confirm_password="1234"), format="json"
        )
        assert response.status_code == 400
        assert "password" in response.json()["errors"]["fields"]

    def test_duplicate_email_is_rejected_case_insensitively(self, client, user):
        response = client.post(self.url, self.payload(email="RIYA@example.com"), format="json")
        assert response.status_code == 400
        assert "email" in response.json()["errors"]["fields"]

    def test_email_is_normalised_to_lowercase(self, client):
        client.post(self.url, self.payload(email="MiXeD@Example.COM"), format="json")
        assert User.objects.filter(email="mixed@example.com").exists()

    def test_soft_deleted_account_still_owns_its_email(self, client, user):
        """The address must stay taken, or two rows collide on the unique index."""
        user.delete()
        response = client.post(self.url, self.payload(email=user.email), format="json")
        assert response.status_code == 400

    def test_first_name_is_required(self, client):
        response = client.post(self.url, self.payload(first_name=""), format="json")
        assert response.status_code == 400


# ---------------------------------------------------------------------- login

class TestLogin:
    url = reverse("auth-login")

    def test_valid_credentials_return_user_and_tokens(self, client, user):
        response = client.post(
            self.url, {"email": user.email, "password": DEFAULT_PASSWORD}, format="json"
        )
        assert response.status_code == 200
        assert response.json()["data"]["user"]["id"] == user.id
        assert response.json()["data"]["tokens"]["access"]

    def test_email_is_case_insensitive(self, client, user):
        response = client.post(
            self.url, {"email": "RIYA@EXAMPLE.COM", "password": DEFAULT_PASSWORD},
            format="json",
        )
        assert response.status_code == 200

    def test_wrong_password_is_401(self, client, user):
        response = client.post(
            self.url, {"email": user.email, "password": "wrong"}, format="json"
        )
        assert response.status_code == 401

    def test_unknown_email_is_401_with_the_same_message(self, client, user):
        """Identical wording, or the endpoint tells you which emails exist."""
        unknown = client.post(
            self.url, {"email": "nobody@example.com", "password": "wrong"}, format="json"
        )
        wrong = client.post(
            self.url, {"email": user.email, "password": "wrong"}, format="json"
        )
        assert unknown.status_code == wrong.status_code == 401
        assert unknown.json()["message"] == wrong.json()["message"]

    def test_deactivated_account_is_403_not_401(self, client, user):
        user.is_active = False
        user.save(update_fields=["is_active"])
        response = client.post(
            self.url, {"email": user.email, "password": DEFAULT_PASSWORD}, format="json"
        )
        assert response.status_code == 403

    def test_deactivated_account_with_wrong_password_is_still_401(self, client, user):
        """Do not reveal 'deactivated' to someone who lacks the password."""
        user.is_active = False
        user.save(update_fields=["is_active"])
        response = client.post(
            self.url, {"email": user.email, "password": "wrong"}, format="json"
        )
        assert response.status_code == 401

    def test_soft_deleted_user_cannot_log_in(self, client, user):
        user.delete()
        response = client.post(
            self.url, {"email": user.email, "password": DEFAULT_PASSWORD}, format="json"
        )
        assert response.status_code == 401


# --------------------------------------------------------------- token / logout

class TestTokens:
    def test_refresh_returns_a_new_access_token(self, client, auth_client):
        response = client.post(
            reverse("auth-token-refresh"),
            {"refresh": auth_client.refresh_token},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["data"]["access"]

    def test_rotation_blacklists_the_old_refresh_token(self, client, auth_client):
        """ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION must both be live."""
        old = auth_client.refresh_token
        first = client.post(reverse("auth-token-refresh"), {"refresh": old}, format="json")
        assert first.status_code == 200
        assert first.json()["data"]["refresh"] != old

        reused = client.post(reverse("auth-token-refresh"), {"refresh": old}, format="json")
        assert reused.status_code == 401

    def test_logout_blacklists_the_refresh_token(self, auth_client, client):
        response = auth_client.post(
            reverse("auth-logout"), {"refresh": auth_client.refresh_token}, format="json"
        )
        assert response.status_code == 200

        reused = client.post(
            reverse("auth-token-refresh"),
            {"refresh": auth_client.refresh_token},
            format="json",
        )
        assert reused.status_code == 401

    def test_logout_is_idempotent(self, auth_client):
        """A client retrying a logout must not see an error."""
        payload = {"refresh": auth_client.refresh_token}
        assert auth_client.post(reverse("auth-logout"), payload, format="json").status_code == 200
        assert auth_client.post(reverse("auth-logout"), payload, format="json").status_code == 200

    def test_logout_requires_authentication(self, client):
        response = client.post(reverse("auth-logout"), {"refresh": "x"}, format="json")
        assert response.status_code == 401


# ------------------------------------------------------------------- passwords

class TestPasswordForgot:
    url = reverse("auth-password-forgot")

    def test_known_email_issues_a_token(self, client, user):
        response = client.post(self.url, {"email": user.email}, format="json")
        assert response.status_code == 200
        assert PasswordResetToken.objects.filter(user=user).count() == 1

    def test_unknown_email_is_also_200_with_the_same_message(self, client, user):
        """Anything else turns this endpoint into an account-existence oracle."""
        known = client.post(self.url, {"email": user.email}, format="json")
        unknown = client.post(self.url, {"email": "nobody@example.com"}, format="json")
        assert known.status_code == unknown.status_code == 200
        assert known.json()["message"] == unknown.json()["message"]
        assert PasswordResetToken.objects.count() == 1

    def test_issuing_a_new_token_invalidates_outstanding_ones(self, client, user):
        client.post(self.url, {"email": user.email}, format="json")
        first = PasswordResetToken.objects.get(user=user)

        client.post(self.url, {"email": user.email}, format="json")
        first.refresh_from_db()

        assert first.used_at is not None
        assert not first.is_valid
        assert PasswordResetToken.objects.filter(user=user, used_at__isnull=True).count() == 1


class TestPasswordReset:
    url = reverse("auth-password-reset")

    @pytest.fixture
    def token(self, client, user):
        client.post(reverse("auth-password-forgot"), {"email": user.email}, format="json")
        return PasswordResetToken.objects.get(user=user, used_at__isnull=True)

    def payload(self, token_value):
        return {
            "token": token_value,
            "password": NEW_PASSWORD,
            "confirm_password": NEW_PASSWORD,
        }

    def test_valid_token_sets_the_new_password(self, client, user, token):
        response = client.post(self.url, self.payload(token.token), format="json")
        assert response.status_code == 200

        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)

    def test_token_is_single_use(self, client, token):
        assert client.post(self.url, self.payload(token.token), format="json").status_code == 200
        assert client.post(self.url, self.payload(token.token), format="json").status_code == 400

    def test_expired_token_is_rejected(self, client, user, token):
        from datetime import timedelta

        from django.utils import timezone

        token.expires_at = timezone.now() - timedelta(seconds=1)
        token.save(update_fields=["expires_at"])

        response = client.post(self.url, self.payload(token.token), format="json")
        assert response.status_code == 400
        user.refresh_from_db()
        assert user.check_password(DEFAULT_PASSWORD)

    def test_unknown_token_is_rejected(self, client):
        response = client.post(self.url, self.payload("not-a-real-token"), format="json")
        assert response.status_code == 400

    def test_reset_ends_existing_sessions(self, client, user, auth_client, token):
        """A live refresh token must not survive a password reset."""
        client.post(self.url, self.payload(token.token), format="json")

        reused = client.post(
            reverse("auth-token-refresh"),
            {"refresh": auth_client.refresh_token},
            format="json",
        )
        assert reused.status_code == 401

    def test_mismatched_confirmation_is_rejected(self, client, token):
        response = client.post(
            self.url,
            {"token": token.token, "password": NEW_PASSWORD, "confirm_password": "nope"},
            format="json",
        )
        assert response.status_code == 400


class TestPasswordChange:
    url = reverse("auth-password-change")

    def test_changes_the_password(self, auth_client, user):
        response = auth_client.post(
            self.url,
            {
                "current_password": DEFAULT_PASSWORD,
                "password": NEW_PASSWORD,
                "confirm_password": NEW_PASSWORD,
            },
            format="json",
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)

    def test_wrong_current_password_is_rejected(self, auth_client, user):
        response = auth_client.post(
            self.url,
            {
                "current_password": "wrong",
                "password": NEW_PASSWORD,
                "confirm_password": NEW_PASSWORD,
            },
            format="json",
        )
        assert response.status_code == 400
        user.refresh_from_db()
        assert user.check_password(DEFAULT_PASSWORD)

    def test_reusing_the_current_password_is_rejected(self, auth_client):
        response = auth_client.post(
            self.url,
            {
                "current_password": DEFAULT_PASSWORD,
                "password": DEFAULT_PASSWORD,
                "confirm_password": DEFAULT_PASSWORD,
            },
            format="json",
        )
        assert response.status_code == 400

    def test_requires_authentication(self, client):
        assert client.post(self.url, {}, format="json").status_code == 401


# ------------------------------------------------------------------- /users/me/

class TestMe:
    url = reverse("me")

    def test_returns_the_documented_shape(self, auth_client, user):
        response = auth_client.get(self.url)
        assert response.status_code == 200

        data = response.json()["data"]
        expected = {
            "id", "email", "first_name", "last_name", "full_name", "phone_number",
            "avatar", "city", "country", "additional_info", "language", "currency",
            "role", "is_email_verified", "created_at",
        }
        assert set(data) == expected
        assert data["full_name"] == user.full_name

    def test_requires_authentication(self, client):
        assert client.get(self.url).status_code == 401

    def test_patch_updates_editable_fields(self, auth_client, user):
        response = auth_client.patch(
            self.url,
            {"first_name": "Riya-Updated", "language": "hi", "currency": "usd"},
            format="json",
        )
        assert response.status_code == 200

        user.refresh_from_db()
        assert user.first_name == "Riya-Updated"
        assert user.language == "hi"
        assert user.currency == "USD", "currency should be upper-cased"

    def test_patch_cannot_escalate_role_or_change_email(self, auth_client, user):
        """Both fields are absent from ProfileUpdateSerializer — silently ignored."""
        auth_client.patch(
            self.url,
            {"role": "ADMIN", "email": "hacker@example.com", "is_staff": True},
            format="json",
        )
        user.refresh_from_db()
        assert user.role == "USER"
        assert user.email == "riya@example.com"
        assert user.is_staff is False

    def test_invalid_currency_length_is_rejected(self, auth_client):
        response = auth_client.patch(self.url, {"currency": "RUPEE"}, format="json")
        assert response.status_code == 400

    def test_delete_soft_deletes_and_deactivates(self, auth_client, user):
        response = auth_client.delete(self.url)
        assert response.status_code == 204
        assert response.content == b"", "204 must not carry a body"

        assert not User.objects.filter(pk=user.pk).exists()
        archived = User.all_objects.get(pk=user.pk)
        assert archived.is_deleted is True
        assert archived.deleted_at is not None
        assert archived.is_active is False

    def test_delete_ends_existing_sessions(self, auth_client, client):
        auth_client.delete(self.url)
        reused = client.post(
            reverse("auth-token-refresh"),
            {"refresh": auth_client.refresh_token},
            format="json",
        )
        assert reused.status_code == 401


class TestMeStats:
    url = reverse("me-stats")

    def test_returns_the_documented_shape(self, auth_client, user):
        """Values are zero until A3; the *shape* is the contract."""
        response = auth_client.get(self.url)
        assert response.status_code == 200

        data = response.json()["data"]
        assert set(data) == {
            "total_trips", "ongoing", "upcoming", "completed",
            "cities_visited", "countries_visited",
            "total_planned_spend", "currency",
        }
        assert data["currency"] == user.currency
        assert isinstance(data["total_planned_spend"], str), "money is a string"

    def test_requires_authentication(self, client):
        assert client.get(self.url).status_code == 401


class TestEnvelope:
    """The envelope is a cross-cutting contract; assert it on real endpoints."""

    def test_success_responses_are_enveloped(self, auth_client):
        body = auth_client.get(reverse("me")).json()
        assert set(body) == {"success", "message", "data"}
        assert body["success"] is True

    def test_error_responses_are_enveloped(self, client):
        body = client.post(
            reverse("auth-login"), {"email": "x@y.com", "password": "z"}, format="json"
        ).json()
        assert set(body) == {"success", "message", "errors"}
        assert body["success"] is False
        assert isinstance(body["message"], str)

    def test_field_errors_are_nested_under_errors_fields(self, client):
        body = client.post(reverse("auth-register"), {"email": "not-an-email"}, format="json").json()
        assert "fields" in body["errors"]
        assert "email" in body["errors"]["fields"]
