"""Custom user (email login) plus the saved-destinations list."""

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Manager for a user keyed on email rather than username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("A superuser must have is_staff and is_superuser set.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Profile fields follow the registration and settings screens."""

    class Language(models.TextChoices):
        EN = "en", "English"
        HI = "hi", "Hindi"
        FR = "fr", "French"
        ES = "es", "Spanish"
        DE = "de", "German"

    username = None
    email = models.EmailField(unique=True)

    phone = models.CharField(max_length=32, blank=True)
    photo = models.ImageField(upload_to="avatars/", blank=True)
    home_city = models.ForeignKey(
        "geo.City",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    home_country = models.ForeignKey(
        "geo.Country",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    additional_info = models.TextField(blank=True)
    language = models.CharField(
        max_length=10, choices=Language.choices, default=Language.EN
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class SavedDestination(models.Model):
    """A city the user bookmarked for later (Profile screen)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_destinations",
    )
    city = models.ForeignKey(
        "geo.City", on_delete=models.CASCADE, related_name="saved_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "city"], name="uniq_saved_destination_user_city"
            )
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.city.name}"
