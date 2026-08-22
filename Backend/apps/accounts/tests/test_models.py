"""
accounts — constraints, properties and `save()` behaviour.

Also the de facto test suite for `core.models.BaseModel`: those bases are
abstract, so `User` is the first concrete model that exercises them.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.constants import UserRole
from apps.accounts.models import PasswordResetToken, User
from apps.accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestUserManager:
    def test_create_user_hashes_the_password(self):
        user = User.objects.create_user(
            email="a@example.com", password="Str0ng-Pass!2026", first_name="A"
        )
        assert user.password != "Str0ng-Pass!2026"
        assert user.check_password("Str0ng-Pass!2026")

    def test_create_user_normalises_the_email(self):
        user = User.objects.create_user(
            email="MiXeD@Example.COM", password="x", first_name="A"
        )
        assert user.email == "mixed@example.com"

    def test_create_user_without_a_password_is_unusable_not_blank(self):
        """An empty hash would let anyone in with an empty password."""
        user = User.objects.create_user(email="a@example.com", first_name="A")
        assert not user.has_usable_password()
        assert not user.check_password("")

    def test_email_is_required(self):
        with pytest.raises(ValueError, match="email address is required"):
            User.objects.create_user(email="", password="x", first_name="A")

    def test_create_superuser_gets_admin_role_and_staff(self):
        """`createsuperuser` must produce someone who can reach /api/v1/admin/."""
        admin = User.objects.create_superuser(
            email="admin@example.com", password="Str0ng-Pass!2026", first_name="Admin"
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == UserRole.ADMIN
        assert admin.is_admin is True


class TestUserProperties:
    def test_full_name_joins_both_names(self):
        assert UserFactory(first_name="Riya", last_name="Sharma").full_name == "Riya Sharma"

    def test_full_name_has_no_trailing_space_without_a_last_name(self):
        assert UserFactory(first_name="Riya", last_name="").full_name == "Riya"

    def test_is_admin_is_true_for_the_admin_role(self):
        assert UserFactory(role=UserRole.ADMIN).is_admin is True

    def test_is_admin_is_true_for_staff_without_the_role(self):
        """The createsuperuser escape hatch — see core.permissions.IsAdminRole."""
        assert UserFactory(role=UserRole.USER, is_staff=True).is_admin is True

    def test_plain_user_is_not_admin(self):
        assert UserFactory().is_admin is False


class TestSoftDelete:
    def test_delete_marks_the_row_instead_of_removing_it(self):
        user = UserFactory()
        user.delete()

        assert not User.objects.filter(pk=user.pk).exists()
        archived = User.all_objects.get(pk=user.pk)
        assert archived.is_deleted is True
        assert archived.deleted_at is not None

    def test_hard_delete_really_removes_the_row(self):
        user = UserFactory()
        user.delete(hard=True)
        assert not User.all_objects.filter(pk=user.pk).exists()

    def test_queryset_delete_also_soft_deletes(self):
        UserFactory.create_batch(3)
        User.objects.all().delete()

        assert User.objects.count() == 0
        assert User.all_objects.count() == 3

    def test_queryset_hard_delete_removes_rows(self):
        UserFactory.create_batch(3)
        User.objects.all().hard_delete()
        assert User.all_objects.count() == 0

    def test_restore_brings_a_row_back(self):
        user = UserFactory()
        user.delete()
        User.all_objects.get(pk=user.pk).restore()

        restored = User.objects.get(pk=user.pk)
        assert restored.is_deleted is False
        assert restored.deleted_at is None

    def test_timestamps_are_populated(self):
        user = UserFactory()
        assert user.created_at is not None
        assert user.updated_at is not None


class TestPasswordResetToken:
    def _token(self, user, **overrides):
        defaults = {
            "user": user,
            "token": "a-token",
            "expires_at": timezone.now() + timedelta(minutes=30),
        }
        return PasswordResetToken.objects.create(**{**defaults, **overrides})

    def test_a_fresh_unused_token_is_valid(self):
        assert self._token(UserFactory()).is_valid is True

    def test_an_expired_token_is_invalid(self):
        token = self._token(
            UserFactory(), expires_at=timezone.now() - timedelta(seconds=1)
        )
        assert token.is_valid is False

    def test_a_spent_token_is_invalid(self):
        token = self._token(UserFactory(), used_at=timezone.now())
        assert token.is_valid is False

    def test_tokens_cascade_when_the_user_is_hard_deleted(self):
        user = UserFactory()
        self._token(user)
        user.delete(hard=True)
        assert PasswordResetToken.objects.count() == 0

    def test_tokens_survive_a_soft_delete(self):
        """
        Soft delete does not cascade — Django's collector bypasses `delete()`.
        Documented in core.models.BaseModel; asserted here so a future change
        to that behaviour is caught rather than discovered.
        """
        user = UserFactory()
        self._token(user)
        user.delete()
        assert PasswordResetToken.objects.filter(user_id=user.pk).count() == 1
