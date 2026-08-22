"""Auth and profile endpoints, mounted under /api/auth/."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.generics import GenericAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from common.permissions import IsOwner

from .models import SavedDestination
from .serializers import (
    AuthResponseSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    SavedDestinationSerializer,
    UserSerializer,
    build_password_reset_tokens,
)

User = get_user_model()


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


@extend_schema(
    summary="Register",
    description="Creates an account and returns the user with a token pair.",
    tags=["Auth"],
    responses={201: AuthResponseSerializer},
)
class RegisterView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "user": UserSerializer(user, context={"request": request}).data,
                **_tokens_for(user),
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    summary="Log in",
    description="Email + password for a token pair and the user object.",
    tags=["Auth"],
    responses={200: AuthResponseSerializer},
)
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


@extend_schema(
    summary="Log out",
    description="Blacklists the refresh token so it cannot be reused.",
    tags=["Auth"],
    responses={204: None},
)
class LogoutView(GenericAPIView):
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Request a password reset",
    description=(
        "Emails a reset link. Always returns 200 -- the response does not "
        "reveal whether the address is registered. In development the mail "
        "is printed to the console."
    ),
    tags=["Auth"],
    responses={200: None},
)
class PasswordResetRequestView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(
            email__iexact=serializer.validated_data["email"], is_active=True
        ).first()
        if user is not None:
            uid, token = build_password_reset_tokens(user)
            link = f"{settings.FRONTEND_PASSWORD_RESET_URL}?uid={uid}&token={token}"
            send_mail(
                subject="Reset your GlobeTrotter password",
                message=(
                    f"Hi {user.full_name},\n\n"
                    f"Use this link to choose a new password:\n{link}\n\n"
                    f"If you did not ask for this, you can ignore this email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

        return Response(
            {"detail": "If that address is registered, a reset link is on its way."}
        )


@extend_schema(
    summary="Confirm a password reset",
    description="Consumes the uid/token from the emailed link.",
    tags=["Auth"],
    responses={200: None},
)
class PasswordResetConfirmView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password updated."})


@extend_schema_view(
    get=extend_schema(summary="Get my profile", tags=["Profile"]),
    put=extend_schema(summary="Replace my profile", tags=["Profile"]),
    patch=extend_schema(
        summary="Update my profile",
        description="Accepts multipart so `photo` can be uploaded here.",
        tags=["Profile"],
    ),
    delete=extend_schema(
        summary="Delete my account",
        description="Permanent. Cascades to the user's trips and saved cities.",
        tags=["Profile"],
        responses={204: None},
    ),
)
class MeView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user


@extend_schema_view(
    list=extend_schema(summary="List my saved destinations", tags=["Profile"]),
    create=extend_schema(summary="Save a destination", tags=["Profile"]),
    destroy=extend_schema(summary="Remove a saved destination", tags=["Profile"]),
)
class SavedDestinationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SavedDestinationSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    owner_field = "user"
    filter_backends = []
    queryset = SavedDestination.objects.none()

    def get_queryset(self):
        return SavedDestination.objects.filter(
            user=self.request.user
        ).select_related("city", "city__country")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
