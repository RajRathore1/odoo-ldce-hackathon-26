from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from geo.models import City, Country

from .models import SavedDestination
from .serializers import build_password_reset_tokens

User = get_user_model()

STRONG = "gl0be-Trotter!2026"


class RegistrationTests(TestCase):
    def payload(self, **overrides):
        data = {
            "email": "ada@example.com",
            "password": STRONG,
            "first_name": "Ada",
            "last_name": "Lovelace",
            "phone": "+44 20 7123 4567",
        }
        return {**data, **overrides}

    def test_register_returns_user_and_token_pair(self):
        res = self.client.post(reverse("register"), self.payload())
        self.assertEqual(res.status_code, 201, res.content)
        body = res.json()
        self.assertEqual(body["user"]["email"], "ada@example.com")
        self.assertEqual(body["user"]["full_name"], "Ada Lovelace")
        self.assertTrue(body["access"] and body["refresh"])
        self.assertNotIn("password", body["user"])

    def test_password_is_hashed_not_stored_plaintext(self):
        self.client.post(reverse("register"), self.payload())
        user = User.objects.get(email="ada@example.com")
        self.assertNotEqual(user.password, STRONG)
        self.assertTrue(user.check_password(STRONG))

    def test_weak_password_is_rejected(self):
        res = self.client.post(reverse("register"), self.payload(password="abc"))
        self.assertEqual(res.status_code, 400)

    def test_password_similar_to_email_is_rejected(self):
        """Proves the unsaved instance reaches UserAttributeSimilarityValidator."""
        res = self.client.post(
            reverse("register"),
            self.payload(email="lovelace@example.com", password="lovelace"),
        )
        self.assertEqual(res.status_code, 400)

    def test_duplicate_email_is_rejected(self):
        self.client.post(reverse("register"), self.payload())
        res = self.client.post(reverse("register"), self.payload())
        self.assertEqual(res.status_code, 400)
        self.assertIn("email", res.json())


class AuthenticatedTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="ada@example.com", password=STRONG, first_name="Ada"
        )
        cls.country = Country.objects.create(name="Japan", code2="JP", continent="AS")
        cls.tokyo = City.objects.create(name="Tokyo", country=cls.country)
        cls.kyoto = City.objects.create(name="Kyoto", country=cls.country)

    def login(self, email="ada@example.com", password=STRONG):
        res = self.client.post(reverse("login"), {"email": email, "password": password})
        self.assertEqual(res.status_code, 200, res.content)
        return res.json()

    def auth(self, access):
        return {"HTTP_AUTHORIZATION": f"Bearer {access}"}


class LoginLogoutTests(AuthenticatedTestCase):
    def test_login_returns_tokens_and_user(self):
        body = self.login()
        self.assertEqual(body["user"]["email"], "ada@example.com")
        self.assertTrue(body["access"] and body["refresh"])

    def test_login_with_wrong_password_fails(self):
        res = self.client.post(
            reverse("login"), {"email": "ada@example.com", "password": "nope"}
        )
        self.assertEqual(res.status_code, 401)

    def test_refresh_issues_a_new_access_token(self):
        body = self.login()
        res = self.client.post(reverse("token-refresh"), {"refresh": body["refresh"]})
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.json())

    def test_logout_blacklists_the_refresh_token(self):
        body = self.login()
        res = self.client.post(
            reverse("logout"), {"refresh": body["refresh"]}, **self.auth(body["access"])
        )
        self.assertEqual(res.status_code, 204)

        reused = self.client.post(reverse("token-refresh"), {"refresh": body["refresh"]})
        self.assertEqual(reused.status_code, 401, "blacklisted token was accepted")

    def test_logout_rejects_a_garbage_token(self):
        body = self.login()
        res = self.client.post(
            reverse("logout"), {"refresh": "not-a-token"}, **self.auth(body["access"])
        )
        self.assertEqual(res.status_code, 400)


class ProfileTests(AuthenticatedTestCase):
    def test_me_requires_authentication(self):
        self.assertEqual(self.client.get(reverse("me")).status_code, 401)

    def test_get_and_patch_profile(self):
        body = self.login()
        headers = self.auth(body["access"])

        res = self.client.get(reverse("me"), **headers)
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.json()["home_city"])

        res = self.client.patch(
            reverse("me"),
            {"last_name": "Lovelace", "home_city": self.tokyo.pk, "language": "fr"},
            content_type="application/json",
            **headers,
        )
        self.assertEqual(res.status_code, 200, res.content)
        updated = res.json()
        self.assertEqual(updated["last_name"], "Lovelace")
        self.assertEqual(updated["language"], "fr")
        # FK written by id, read back nested.
        self.assertEqual(updated["home_city"], self.tokyo.pk)
        self.assertEqual(updated["home_city_detail"]["name"], "Tokyo")

    def test_delete_account_is_permanent(self):
        body = self.login()
        res = self.client.delete(reverse("me"), **self.auth(body["access"]))
        self.assertEqual(res.status_code, 204)
        self.assertFalse(User.objects.filter(email="ada@example.com").exists())


class SavedDestinationTests(AuthenticatedTestCase):
    def test_save_list_and_delete(self):
        headers = self.auth(self.login()["access"])
        url = reverse("saved-destination-list")

        res = self.client.post(url, {"city": self.tokyo.pk}, **headers)
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.json()["city_detail"]["name"], "Tokyo")
        saved_id = res.json()["id"]

        res = self.client.get(url, **headers)
        self.assertEqual(res.json()["count"], 1)

        res = self.client.delete(
            reverse("saved-destination-detail", args=[saved_id]), **headers
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(SavedDestination.objects.count(), 0)

    def test_saving_the_same_city_twice_is_a_400_not_a_500(self):
        headers = self.auth(self.login()["access"])
        url = reverse("saved-destination-list")
        self.client.post(url, {"city": self.tokyo.pk}, **headers)
        res = self.client.post(url, {"city": self.tokyo.pk}, **headers)
        self.assertEqual(res.status_code, 400, res.content)

    def test_users_cannot_see_or_delete_another_users_saves(self):
        other = User.objects.create_user(email="bob@example.com", password=STRONG)
        theirs = SavedDestination.objects.create(user=other, city=self.kyoto)

        headers = self.auth(self.login()["access"])
        res = self.client.get(reverse("saved-destination-list"), **headers)
        self.assertEqual(res.json()["count"], 0)

        res = self.client.delete(
            reverse("saved-destination-detail", args=[theirs.pk]), **headers
        )
        self.assertEqual(res.status_code, 404)
        self.assertTrue(SavedDestination.objects.filter(pk=theirs.pk).exists())


class PasswordResetTests(AuthenticatedTestCase):
    def test_request_sends_mail_and_confirm_changes_the_password(self):
        res = self.client.post(reverse("password-reset"), {"email": "ada@example.com"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset-password", mail.outbox[0].body)

        uid, token = build_password_reset_tokens(self.user)
        new_password = "Sk1es-Above!2026"
        res = self.client.post(
            reverse("password-reset-confirm"),
            {"uid": uid, "token": token, "new_password": new_password},
        )
        self.assertEqual(res.status_code, 200, res.content)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.login(password=new_password)

    def test_unknown_email_still_returns_200_but_sends_nothing(self):
        """Must not leak which addresses are registered."""
        res = self.client.post(
            reverse("password-reset"), {"email": "nobody@example.com"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_token_cannot_be_reused(self):
        uid, token = build_password_reset_tokens(self.user)
        payload = {"uid": uid, "token": token, "new_password": "Sk1es-Above!2026"}
        self.assertEqual(
            self.client.post(reverse("password-reset-confirm"), payload).status_code,
            200,
        )
        # Changing the hash invalidates the token.
        res = self.client.post(reverse("password-reset-confirm"), payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("token", res.json())

    def test_tampered_token_and_uid_are_rejected(self):
        uid, token = build_password_reset_tokens(self.user)
        cases = [
            ({"uid": uid, "token": "bogus-token"}, "token"),
            ({"uid": "bogus-uid", "token": token}, "uid"),
        ]
        for overrides, expected_key in cases:
            with self.subTest(**overrides):
                res = self.client.post(
                    reverse("password-reset-confirm"),
                    {"new_password": "Sk1es-Above!2026", **overrides},
                )
                self.assertEqual(res.status_code, 400)
                self.assertIn(expected_key, res.json())

    def test_weak_new_password_is_rejected(self):
        uid, token = build_password_reset_tokens(self.user)
        res = self.client.post(
            reverse("password-reset-confirm"),
            {"uid": uid, "token": token, "new_password": "123"},
        )
        self.assertEqual(res.status_code, 400)
