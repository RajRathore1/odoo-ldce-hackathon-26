"""
accounts — views. Owner: Dev A.

Thin. Parse the request, call a service or selector, return a response.
No business rules and no multi-step ORM work.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView

from apps.accounts import selectors, services
from apps.accounts.serializers import (
    AvatarSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordChangeSerializer,
    PasswordForgotSerializer,
    PasswordResetSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)
from core.response import created, no_content, success


@extend_schema(tags=["auth"])
class RegisterView(GenericAPIView):
    """Create an account. Returns the user and an immediately usable token pair."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, tokens = services.register_user(**serializer.validated_data)
        return created(
            data={
                "user": UserSerializer(user, context={"request": request}).data,
                "tokens": tokens,
            },
            message="Account created successfully.",
        )


@extend_schema(tags=["auth"])
class LoginView(GenericAPIView):
    """
    Email + password. Same `data` shape as register, so the frontend has one
    code path for "you are now signed in".
    """

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return success(
            data={
                "user": UserSerializer(user, context={"request": request}).data,
                "tokens": services.login_user(user),
            },
            message="Signed in successfully.",
        )


@extend_schema(tags=["auth"])
class TokenRefreshView(BaseTokenRefreshView):
    """
    SimpleJWT's view, re-exported so it carries our `auth` schema tag and lives
    in our URL module rather than being imported into it.

    `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION` mean the response
    includes a *new* refresh token and the old one is dead — the client must
    store the new one.
    """

    permission_classes = [AllowAny]


@extend_schema(tags=["auth"])
class LogoutView(GenericAPIView):
    """Blacklist a refresh token. Idempotent — a spent token is still a 200."""

    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.logout_user(serializer.validated_data["refresh"])
        return success(message="Signed out successfully.")


@extend_schema(tags=["auth"])
class PasswordForgotView(GenericAPIView):
    """
    Issue a reset token.

    **Always 200**, whether or not the address exists — a 404 here would let
    anyone test which emails have accounts. In dev the token is logged to the
    console.
    """

    serializer_class = PasswordForgotSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.issue_password_reset_token(serializer.validated_data["email"])
        return success(
            message="If that email exists, a reset link has been sent.",
        )


@extend_schema(tags=["auth"])
class PasswordResetView(GenericAPIView):
    """Consume a reset token and set a new password. Ends every session."""

    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.reset_password(
            serializer.validated_data["token"], serializer.validated_data["password"]
        )
        return success(message="Password reset. You can now sign in.")


@extend_schema(tags=["auth"])
class PasswordChangeView(GenericAPIView):
    """
    Change password while signed in.

    Every session ends, including this one — the client must sign in again.
    That is deliberate: it is the only way to be certain a leaked token is gone.
    """

    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.change_password(request.user, serializer.validated_data["password"])
        return success(message="Password changed. Please sign in again.")


# ------------------------------------------------------------------- /users/me/

@extend_schema_view(
    get=extend_schema(tags=["profile"], summary="Current profile"),
    patch=extend_schema(tags=["profile"], summary="Update profile"),
    delete=extend_schema(tags=["profile"], summary="Delete account"),
)
class MeView(GenericAPIView):
    """`GET`, `PATCH` and `DELETE` on the caller's own account."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return ProfileUpdateSerializer if self.request.method == "PATCH" else UserSerializer

    def get_object(self):
        # Joined so the nested city/country cost no extra queries.
        return selectors.user_with_relations(self.request.user.pk)

    def get(self, request):
        return success(
            data=UserSerializer(self.get_object(), context={"request": request}).data
        )

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            instance=request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success(
            data=UserSerializer(
                self.get_object(), context={"request": request}
            ).data,
            message="Profile updated.",
        )

    def delete(self, request):
        services.delete_account(request.user)
        return no_content()


@extend_schema(tags=["profile"], request=AvatarSerializer, responses={200: UserSerializer})
class AvatarView(GenericAPIView):
    """`multipart/form-data`, field `avatar`."""

    serializer_class = AvatarSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = self.get_serializer(instance=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success(
            data=UserSerializer(request.user, context={"request": request}).data,
            message="Avatar updated.",
        )


@extend_schema(tags=["profile"], summary="Profile header counters")
class MeStatsView(APIView):
    """
    Counters for the Screen 12 header.

    ⚠️ Returns zeros until task A3 — every figure aggregates over `trips`,
    which does not exist yet. The shape is final; see
    `selectors.user_stats`.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = selectors.user_stats(request.user)
        # Money as a string, matching every other amount in the API — see the
        # COERCE_DECIMAL_TO_STRING note in config/settings/base.py.
        return success(
            data={**stats, "total_planned_spend": str(stats["total_planned_spend"])}
        )
