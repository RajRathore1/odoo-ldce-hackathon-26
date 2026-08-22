"""
accounts — Django admin. Owner: Dev A.

Registrations for `/django-admin/`. Worth keeping current: it is how we
fix data by hand mid-demo.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import PasswordResetToken, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Subclasses Django's `UserAdmin` so the password field stays a hash widget
    with a "change password" form rather than a plain text input — a
    `ModelAdmin` would happily let you save a raw string as the hash and lock
    the account out.

    Every fieldset is redeclared because our `USERNAME_FIELD` is `email` and
    there is no `username` or `date_joined` for the parent's defaults to find.
    """

    ordering = ("-created_at",)
    list_display = ("email", "full_name", "role", "city", "is_active", "created_at")
    list_filter = ("role", "is_active", "is_staff", "is_email_verified", "is_deleted")
    search_fields = ("email", "first_name", "last_name", "phone_number")
    list_select_related = ("city",)
    autocomplete_fields = ("city", "country")
    readonly_fields = ("created_at", "updated_at", "last_login", "deleted_at")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Profile",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                    "avatar",
                    "city",
                    "country",
                    "additional_info",
                )
            },
        ),
        ("Preferences", {"fields": ("language", "currency")}),
        (
            "Permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_email_verified",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Soft delete", {"fields": ("is_deleted", "deleted_at")}),
        ("Timestamps", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "password1", "password2"),
            },
        ),
    )

    def get_queryset(self, request):
        """
        Show soft-deleted users too. An admin looking at the user list needs to
        see a deactivated account in order to restore it; the default manager
        hides them.
        """
        return User.all_objects.all()

    @admin.display(description="Name", ordering="first_name")
    def full_name(self, obj) -> str:
        return obj.full_name


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "expires_at", "used_at", "is_valid", "created_at")
    list_filter = ("used_at",)
    search_fields = ("user__email", "token")
    list_select_related = ("user",)
    readonly_fields = ("token", "user", "expires_at", "used_at")

    @admin.display(boolean=True, description="Valid")
    def is_valid(self, obj) -> bool:
        return obj.is_valid
