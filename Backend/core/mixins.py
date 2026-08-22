"""
View mixins.

The important one is `OwnerQuerysetMixin`: **object permissions do not filter
lists.** `IsOwner` runs on `get_object()`, so without scoping the queryset a
list endpoint happily returns every user's rows. Scope at the queryset, and use
the permission class as the second line of defence for detail routes.
"""

from core.permissions import IsAdminRole


class OwnerQuerysetMixin:
    """
    Restrict a list/detail queryset to the caller's own rows.

    Set `owner_field` when the FK is not called `user`:

        class ExpenseViewSet(OwnerQuerysetMixin, ModelViewSet):
            owner_field = "trip__user"
    """

    owner_field: str = "user"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not (user and user.is_authenticated):
            return queryset.none()
        return queryset.filter(**{self.owner_field: user})


class AdminOnlyMixin:
    """
    Inherit this on **every** view under `/api/v1/admin/`.

    DRF resolves permissions per view, so there is no way to attach
    `IsAdminRole` to a URL subtree from `config/admin_urls.py` — and a JWT user
    is not available to middleware either, because authentication happens
    inside the DRF view, not before it. This mixin is the enforcement point.

        class AdminUserViewSet(AdminOnlyMixin, ModelViewSet):
            ...

    A view that forgets it falls back to the global default of
    `IsAuthenticated`, which means any logged-in user reaches an admin
    endpoint. Task B6.7 tests the whole tree for exactly that.
    """

    permission_classes = [IsAdminRole]


class SerializerActionMixin:
    """
    Pick a serializer per action instead of branching on `self.action` in
    `get_serializer_class()`, so read and write shapes stay separate classes.

        serializer_classes = {
            "list": TripListSerializer,
            "retrieve": TripDetailSerializer,
            "create": TripCreateSerializer,
            "update": TripCreateSerializer,
            "partial_update": TripCreateSerializer,
        }
    """

    serializer_classes: dict = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(
            getattr(self, "action", None), super().get_serializer_class()
        )
