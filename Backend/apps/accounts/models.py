"""
accounts — models. Owner: Dev A.

`User`, `PasswordResetToken` — see docs/MODELS.md §3.

Email is the login. Everything from the registration mockup lives on `User` —
no separate Profile table, it would only cost a join.
"""

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from apps.accounts.constants import UserRole
from apps.accounts.managers import AllUsersManager, UserManager
from core.models import BaseModel


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    `date_joined` is deliberately absent — `created_at` from `BaseModel` is the
    same thing, and two fields meaning one thing drift apart.

    `city` / `country` FKs into `geo` are added in task A2, once those models
    exist. They cannot be declared before then: a string reference like
    `"geo.City"` defers the *import*, but Django's system checks still resolve
    the target at startup, so declaring one early stops the project booting.
    """

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="users/avatars/", null=True, blank=True)

    additional_info = models.TextField(blank=True)
    language = models.CharField(max_length=10, default="en")
    currency = models.CharField(max_length=3, default="INR")

    role = models.CharField(
        max_length=10, choices=UserRole.choices, default=UserRole.USER, db_index=True
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    objects = UserManager()
    all_objects = AllUsersManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    class Meta:
        ordering = ("-created_at",)
        # Both managers are declared above; be explicit about which one Django
        # treats as `_default_manager` so related lookups never see deleted rows.
        default_manager_name = "objects"

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_admin(self) -> bool:
        """Read by `core.permissions.IsAdminRole`."""
        return self.is_staff or self.role == UserRole.ADMIN
