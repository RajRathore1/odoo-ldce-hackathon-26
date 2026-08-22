"""
accounts — managers. Owner: Dev A.

`UserManager` has to do two jobs at once: Django's `create_user` /
`create_superuser` contract, and `BaseModel`'s soft-delete filtering. Building it
off `SoftDeleteQuerySet` keeps both.
"""

from django.contrib.auth.base_user import BaseUserManager

from core.models import SoftDeleteQuerySet


class UserManager(BaseUserManager.from_queryset(SoftDeleteQuerySet)):
    """Default manager: email is the identifier, soft-deleted users are hidden."""

    use_in_migrations = True

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        # set_password even when password is None — that stores an unusable hash
        # rather than an empty one, so the account cannot be logged into.
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        from apps.accounts.constants import UserRole

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class AllUsersManager(BaseUserManager.from_queryset(SoftDeleteQuerySet)):
    """Escape hatch matching `BaseModel.all_objects` — includes deleted users."""
