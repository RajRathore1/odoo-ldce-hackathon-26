"""
The `/api/v1/admin/**` tree, swept as a whole (task B6.7).

A project-level test, because what it asserts is a property of the *tree*, not
of any one view: `config/admin_urls.py` cannot gate its own subtree — DRF
resolves permission classes per view, and a JWT identity is invisible to
middleware because authentication happens inside the view. So every admin view
has to carry `core.mixins.AdminOnlyMixin` itself, and a view that forgets it
silently falls back to the global `IsAuthenticated` default.

This module walks the URL tree and checks every route, so **a new admin endpoint
that forgets the mixin fails here without anybody remembering to write a test
for it**. That is the whole point of doing it this way rather than one assertion
per view.
"""

import pytest
from django.urls import get_resolver, reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, AdminFactory, UserFactory

pytestmark = pytest.mark.django_db

#: `auth/login/` is the one route that may not be admin-gated: you cannot
#: require an admin token in order to obtain one. It gates inside its serializer,
#: and `TestAdminLogin` below covers it.
UNGATED = {"admin-login"}


def admin_routes() -> list[tuple[str, str]]:
    """
    Every `(name, concrete path)` under the admin tree, from the URL conf.

    Read off the resolver rather than hard-coded, so the sweep grows by itself
    as endpoints are added.
    """
    resolver = get_resolver()
    routes = []
    for name in resolver.reverse_dict:
        if not (isinstance(name, str) and name.startswith("admin-")):
            continue
        if name in UNGATED:
            continue
        pattern = resolver.reverse_dict[name][0][0][0]
        routes.append((name, "/" + pattern % {"pk": 1, "user_id": 1}))
    return sorted(routes)


def signed_in(user) -> APIClient:
    api = APIClient()
    response = api.post(
        reverse("auth-login"),
        {"email": user.email, "password": DEFAULT_PASSWORD},
        format="json",
    )
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['tokens']['access']}")
    return api


class TestAdminTreeIsGated:
    def test_the_sweep_actually_found_the_routes(self):
        """Guard against the sweep passing because it tested nothing."""
        assert len(admin_routes()) >= 14

    @pytest.mark.parametrize(("name", "path"), admin_routes())
    def test_an_ordinary_logged_in_user_gets_403(self, name, path):
        """
        Trap #8, swept. A missing `AdminOnlyMixin` shows up as a 200/404 here
        rather than as somebody reading every email address on the platform.
        """
        response = signed_in(UserFactory()).get(path)

        assert response.status_code == 403, f"{name} ({path}) answered {response.status_code}"

    @pytest.mark.parametrize(("name", "path"), admin_routes())
    def test_anonymous_gets_401(self, name, path):
        response = APIClient().get(path)

        assert response.status_code == 401, f"{name} ({path}) answered {response.status_code}"

    @pytest.mark.parametrize(("name", "path"), admin_routes())
    def test_a_write_from_an_ordinary_user_gets_403_too(self, name, path):
        """Permissions run before method resolution, so even a POST to a
        read-only route must be refused rather than 405'd."""
        response = signed_in(UserFactory()).post(path, {}, format="json")

        assert response.status_code == 403, f"{name} ({path}) answered {response.status_code}"

    @pytest.mark.parametrize(("name", "path"), admin_routes())
    def test_an_admin_is_not_refused(self, name, path):
        """
        The other half of the check: gated, but not gated *shut*. Anything but
        401/403 is fine — 404 for id 1 is expected on an empty database.
        """
        response = signed_in(AdminFactory(email="sweep-admin@example.com")).get(path)

        assert response.status_code not in (401, 403), f"{name} ({path})"


class TestAdminLogin:
    url = reverse("admin-login")

    def test_an_admin_gets_a_token_pair(self):
        admin = AdminFactory(email="admin@globetrotter.dev", first_name="Ada")

        response = APIClient().post(
            self.url, {"email": admin.email, "password": DEFAULT_PASSWORD}, format="json"
        )
        body = response.json()

        assert response.status_code == 200
        assert body["message"] == "Signed in successfully."
        assert body["data"]["tokens"]["access"]
        assert body["data"]["tokens"]["refresh"]
        assert body["data"]["user"]["email"] == admin.email
        assert body["data"]["user"]["role"] == "ADMIN"

    def test_a_django_superuser_can_sign_in(self):
        """
        The `createsuperuser` escape hatch: one User table, so the credentials
        made for `/django-admin/` work here directly.
        """
        staff = UserFactory(email="root@example.com", is_staff=True)

        response = APIClient().post(
            self.url, {"email": staff.email, "password": DEFAULT_PASSWORD}, format="json"
        )

        assert response.status_code == 200
        assert response.json()["data"]["user"]["is_staff"] is True

    def test_a_correct_password_from_an_ordinary_user_is_a_403(self):
        """
        The reason this endpoint exists. Without the check the admin panel would
        hand a session to any registered user and find out one request later.
        """
        user = UserFactory(email="riya@example.com")

        response = APIClient().post(
            self.url, {"email": user.email, "password": DEFAULT_PASSWORD}, format="json"
        )

        assert response.status_code == 403
        assert "administrator" in response.json()["message"].lower()

    def test_a_wrong_password_is_a_401_not_a_403(self):
        """A 403 here would confirm that the address belongs to an admin."""
        AdminFactory(email="admin@globetrotter.dev")

        response = APIClient().post(
            self.url,
            {"email": "admin@globetrotter.dev", "password": "not-the-password"},
            format="json",
        )

        assert response.status_code == 401

    def test_an_unknown_email_is_a_401(self):
        response = APIClient().post(
            self.url, {"email": "nobody@example.com", "password": "whatever"}, format="json"
        )

        assert response.status_code == 401

    def test_a_deactivated_admin_cannot_sign_in(self):
        admin = AdminFactory(email="admin@globetrotter.dev", is_active=False)

        response = APIClient().post(
            self.url, {"email": admin.email, "password": DEFAULT_PASSWORD}, format="json"
        )

        assert response.status_code == 403

    def test_the_password_is_never_echoed_back(self):
        AdminFactory(email="admin@globetrotter.dev")

        response = APIClient().post(
            self.url,
            {"email": "admin@globetrotter.dev", "password": DEFAULT_PASSWORD},
            format="json",
        )

        assert DEFAULT_PASSWORD not in response.content.decode()

    def test_the_token_works_on_the_admin_tree(self):
        """End to end: sign in here, then use the token where it matters."""
        admin = AdminFactory(email="admin@globetrotter.dev")
        api = APIClient()
        tokens = api.post(
            self.url, {"email": admin.email, "password": DEFAULT_PASSWORD}, format="json"
        ).json()["data"]["tokens"]
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        assert api.get(reverse("admin-user-list")).status_code == 200
        assert api.get(reverse("admin-analytics-overview")).status_code == 200
