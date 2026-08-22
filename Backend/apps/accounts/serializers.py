"""
accounts — serializers. Owner: Dev A.

Field validation and read shaping **only**. Multi-model writes and side effects
live in `services.py`.

Read and write shapes are separate classes on purpose: overloading one
serializer with `context` branching is how a write field ends up readable on a
public endpoint.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

from apps.accounts.models import User

# --------------------------------------------------------------------- nested


class CityBriefSerializer(serializers.Serializer):
    """
    The `{id, name}` shape `API.md` nests inside a user payload.

    Declared here rather than imported from `apps.geo.serializers` because that
    module is Dev B's — importing it would couple our auth endpoints to their
    file and reverse the ownership split. `accounts -> geo` is a legal import
    direction, but not for a serializer someone else is actively editing.
    """

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    state = serializers.CharField(read_only=True)


class CountryBriefSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    iso2 = serializers.CharField(read_only=True)


# ----------------------------------------------------------------------- read


class UserSerializer(serializers.ModelSerializer):
    """Full profile. `GET /users/me/` and the `user` key in auth responses."""

    full_name = serializers.CharField(read_only=True)
    city = CityBriefSerializer(read_only=True)
    country = CountryBriefSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "avatar",
            "city",
            "country",
            "additional_info",
            "language",
            "currency",
            "role",
            "is_email_verified",
            "created_at",
        )
        read_only_fields = ("id", "email", "role", "is_email_verified", "created_at")


class PublicUserSerializer(serializers.ModelSerializer):
    """
    The **only** shape allowed on a public endpoint.

    Used by the shared-trip page. Deliberately minimal: no email, no last name,
    no phone. See the PII trap in CLAUDE.md.
    """

    class Meta:
        model = User
        fields = ("first_name", "avatar")


# ---------------------------------------------------------------------- write


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "confirm_password",
            "first_name",
            "last_name",
            "phone_number",
            "city",
            "country",
            "additional_info",
        )
        extra_kwargs = {
            "first_name": {"required": True, "allow_blank": False},
            "city": {"required": False, "allow_null": True},
            "country": {"required": False, "allow_null": True},
        }

    def validate_email(self, value: str) -> str:
        """
        Case-insensitive uniqueness. `unique=True` on the column is
        case-*sensitive* on SQLite for non-ASCII and unreliable across backends,
        so "Riya@x.com" would otherwise register alongside "riya@x.com" and then
        fail to log in.

        `all_objects` on purpose: a soft-deleted account still owns its address.
        """
        email = value.strip().lower()
        if User.all_objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError(
                {"confirm_password": "The two password fields do not match."}
            )
        _run_password_validators(attrs["password"])
        return attrs


class LoginSerializer(serializers.Serializer):
    """
    Email + password. Not a SimpleJWT `TokenObtainPairSerializer` subclass —
    that one returns a bare `{access, refresh}`, and `API.md` promises the same
    `{user, tokens}` shape as register. `services.login` builds that.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs: dict) -> dict:
        email = attrs["email"].strip().lower()
        password = attrs["password"]

        user = authenticate(
            request=self.context.get("request"), username=email, password=password
        )
        if user is not None:
            attrs["user"] = user
            return attrs

        # `authenticate()` returns None for *both* wrong credentials and an
        # inactive account — ModelBackend.user_can_authenticate rejects
        # is_active=False before we ever see it. API.md distinguishes them
        # (401 vs 403), so check explicitly.
        #
        # This only reveals "deactivated" to someone who already supplied the
        # correct password, so it is not an enumeration oracle.
        candidate = User.objects.filter(email__iexact=email).first()
        if candidate and not candidate.is_active and candidate.check_password(password):
            raise PermissionDenied(
                "This account has been deactivated. Contact an administrator."
            )

        # One message covering "no such account" and "wrong password".
        raise AuthenticationFailed("Incorrect email or password.")


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    `PATCH /users/me/`. Note what is absent: `email`, `role`, `is_active`,
    `avatar`. Email and role must not be self-service, and avatar has its own
    multipart endpoint.
    """

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone_number",
            "city",
            "country",
            "additional_info",
            "language",
            "currency",
        )

    def validate_currency(self, value: str) -> str:
        if value and len(value) != 3:
            raise serializers.ValidationError("Use a 3-letter ISO currency code.")
        return value.upper()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)


class PasswordChangeSerializer(serializers.Serializer):
    """`POST /auth/password/change/` — logged in, knows the old password."""

    current_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_current_password(self, value: str) -> str:
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Your current password is incorrect.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "The two password fields do not match."}
            )
        if attrs["password"] == attrs["current_password"]:
            raise serializers.ValidationError(
                {"password": "The new password must differ from the current one."}
            )
        _run_password_validators(attrs["password"], user=self.context["request"].user)
        return attrs


class PasswordForgotSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetSerializer(serializers.Serializer):
    """
    `POST /auth/password/reset/`. The token is validated in `services` rather
    than here — whether a token is spent is state, not field validation, and the
    service is what marks it used inside a transaction.
    """

    token = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "The two password fields do not match."}
            )
        _run_password_validators(attrs["password"])
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


# -------------------------------------------------------------------- helpers


def _run_password_validators(password: str, user=None) -> None:
    """
    Bridge Django's `AUTH_PASSWORD_VALIDATORS` into DRF's error shape.

    Django raises `django.core.exceptions.ValidationError`; DRF only understands
    its own. Without this the settings-configured validators would be skipped
    entirely and "1234" would be an acceptable password.
    """
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError({"password": list(exc.messages)}) from exc


# ---------------------------------------------------------------------- admin


class AdminLoginSerializer(LoginSerializer):
    """
    `POST /admin/auth/login/` — the Admin Panel's sign-in.

    Same credentials as the user API, because there is one `User` table: a
    `createsuperuser` account or anyone with `role == ADMIN` gets in. The extra
    rule is the point — a valid password from an ordinary user is a **403**, not
    a token. Without that check the admin panel would hand a session to any
    registered user and only discover the problem one request later.
    """

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        if not attrs["user"].is_admin:
            raise PermissionDenied("This account does not have administrator access.")
        return attrs


class AdminUserSerializer(serializers.ModelSerializer):
    """
    One row of `GET /admin/users/`.

    Wider than any user-facing shape on purpose — this is the moderation table,
    so it shows email, role and the deleted flag. It is why the admin tree has
    its own serializers: a user endpoint must never be able to reach this class.
    """

    full_name = serializers.CharField(read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True, default=None)
    country_name = serializers.CharField(source="country.name", read_only=True, default=None)
    trips_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "role",
            "is_active",
            "is_staff",
            "is_email_verified",
            "is_deleted",
            "city_name",
            "country_name",
            "trips_count",
            "posts_count",
            "last_login",
            "created_at",
        )

    def get_trips_count(self, user) -> int:
        """From the selector's annotation — never a query per row."""
        return getattr(user, "trips_count", 0)

    def get_posts_count(self, user) -> int:
        """Always 0: the community app is P2 and cut. The key stays for the UI."""
        return 0


class AdminUserDetailSerializer(AdminUserSerializer):
    """`GET /admin/users/{id}/` — the row plus the rest of the profile."""

    class Meta(AdminUserSerializer.Meta):
        fields = (
            *AdminUserSerializer.Meta.fields,
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "additional_info",
            "language",
            "currency",
            "deleted_at",
            "updated_at",
        )


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """
    `PATCH /admin/users/{id}/` — exactly three fields.

    Not the whole model: an admin moderates accounts, they do not edit somebody's
    phone number or currency. Narrow on purpose, so this endpoint cannot become
    a general-purpose user editor by accident.
    """

    class Meta:
        model = User
        fields = ("is_active", "role", "is_staff")
