"""Serializers for registration, login, profile and saved destinations."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import DjangoUnicodeDecodeError, force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from geo.models import City, Country
from geo.serializers import CitySlimSerializer, CountrySlimSerializer

from .models import SavedDestination

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """The profile payload: FKs are written by id, read back nested."""

    home_city = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), allow_null=True, required=False
    )
    home_country = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), allow_null=True, required=False
    )
    home_city_detail = CitySlimSerializer(source="home_city", read_only=True)
    home_country_detail = CountrySlimSerializer(source="home_country", read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "photo",
            "home_city",
            "home_city_detail",
            "home_country",
            "home_country_detail",
            "additional_info",
            "language",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    """Signup. Fields mirror the registration screen."""

    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    home_city = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), allow_null=True, required=False
    )
    home_country = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
            "phone",
            "photo",
            "home_city",
            "home_country",
            "additional_info",
            "language",
        ]

    def validate(self, attrs):
        # Pass an unsaved instance so UserAttributeSimilarityValidator can
        # compare the password against the name and email being submitted.
        validate_password(
            attrs["password"],
            User(
                email=attrs.get("email", ""),
                first_name=attrs.get("first_name", ""),
                last_name=attrs.get("last_name", ""),
            ),
        )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class AuthResponseSerializer(serializers.Serializer):
    """Response body shared by register and login. Documentation only."""

    user = UserSerializer(read_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)


class LoginSerializer(TokenObtainPairSerializer):
    """Token pair plus the user object, so login is a single round trip."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user, context=self.context).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)

    def validate_refresh(self, value):
        try:
            self._token = RefreshToken(value)
        except TokenError:
            raise serializers.ValidationError("Invalid or expired refresh token.")
        return value

    def save(self, **kwargs):
        self._token.blacklist()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Validates the emailed uid/token pair and sets the new password."""

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        try:
            pk = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=pk)
        except (
            User.DoesNotExist,
            DjangoUnicodeDecodeError,
            ValueError,
            TypeError,
            OverflowError,
        ):
            raise serializers.ValidationError({"uid": "Invalid reset link."})

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError(
                {"token": "Invalid or expired reset link."}
            )

        validate_password(attrs["new_password"], user)
        self._user = user
        return attrs

    def save(self, **kwargs):
        self._user.set_password(self.validated_data["new_password"])
        self._user.save(update_fields=["password"])
        return self._user


class SavedDestinationSerializer(serializers.ModelSerializer):
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())
    city_detail = CitySlimSerializer(source="city", read_only=True)

    class Meta:
        model = SavedDestination
        fields = ["id", "city", "city_detail", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_city(self, city):
        # The (user, city) constraint spans a field the client never sends,
        # so DRF cannot derive this check -- without it a repeat save is a 500.
        if SavedDestination.objects.filter(
            user=self.context["request"].user, city=city
        ).exists():
            raise serializers.ValidationError("This city is already saved.")
        return city


def build_password_reset_tokens(user):
    """uid/token pair for the reset link. Shared by the view and its tests."""
    return (
        urlsafe_base64_encode(force_bytes(user.pk)),
        default_token_generator.make_token(user),
    )
