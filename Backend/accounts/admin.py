from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import SavedDestination, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Rebuilt fieldsets: there is no username, and email is the login."""

    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "is_staff", "is_active"]
    list_filter = ["is_staff", "is_superuser", "is_active", "language"]
    search_fields = ["email", "first_name", "last_name", "phone"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Profile",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone",
                    "photo",
                    "home_city",
                    "home_country",
                    "additional_info",
                    "language",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    autocomplete_fields = ["home_city", "home_country"]


@admin.register(SavedDestination)
class SavedDestinationAdmin(admin.ModelAdmin):
    list_display = ["user", "city", "created_at"]
    search_fields = ["user__email", "city__name"]
    autocomplete_fields = ["user", "city"]
