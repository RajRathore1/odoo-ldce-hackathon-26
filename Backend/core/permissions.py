"""
Shared permission classes. Prefer these over per-app ones — ownership means the
same thing everywhere, and one implementation means one place to get it right.

DRF's global default is `IsAuthenticated` (see `config/settings/base.py`), so a
view only needs to name a class here when it wants *more* than "logged in", or
`AllowAny` when it wants less.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminRole(BasePermission):
    """
    Gate for the whole `/api/v1/admin/` tree.

    Accepts either our own `role == ADMIN` or Django's `is_staff`, so a
    superuser created with `createsuperuser` can always get in — during a demo
    that escape hatch is worth having.
    """

    message = "Administrator access is required."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        # `is_admin` is a property on our User model (accounts.models). getattr
        # keeps this class importable before that model exists.
        return bool(getattr(user, "is_admin", False) or user.is_staff)


class IsOwner(BasePermission):
    """
    Object-level: `obj.user` must be the caller.

    ⚠️ Object permissions only run when the view calls
    `get_object()` / `check_object_permissions()`. For lists, filter the queryset
    by owner instead — see `core.mixins.OwnerQuerysetMixin`. A permission class
    cannot hide rows from a list.
    """

    message = "You do not have permission to act on this resource."

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "user", None)
        return owner is not None and owner == request.user


class IsTripOwner(BasePermission):
    """
    Object-level ownership for anything hanging off a trip.

    Resolves the owning trip from `Trip` itself, `obj.trip`, or
    `obj.trip_stop.trip` — which covers `TripStop`, `TripActivity` and `Expense`
    without each of them needing its own permission class.
    """

    message = "You do not have permission to act on this trip."

    @staticmethod
    def _owner_of(obj):
        for path in ("user", "trip.user", "trip_stop.trip.user"):
            target = obj
            for attribute in path.split("."):
                target = getattr(target, attribute, None)
                if target is None:
                    break
            else:
                return target
        return None

    def has_object_permission(self, request, view, obj):
        owner = self._owner_of(obj)
        return owner is not None and owner == request.user


class IsPublicOrOwner(BasePermission):
    """
    Read a trip if it is shared publicly **or** you own it. Writes stay
    owner-only. Used by the public share endpoints.
    """

    message = "This trip is not shared publicly."

    def has_object_permission(self, request, view, obj):
        owner = IsTripOwner._owner_of(obj)
        if owner is not None and owner == request.user:
            return True
        return request.method in SAFE_METHODS and bool(getattr(obj, "is_public", False))


class IsSelfOrAdmin(BasePermission):
    """For `/users/{id}/`-shaped routes: the user themselves, or an admin."""

    message = "You may only act on your own account."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if bool(getattr(user, "is_admin", False) or user.is_staff):
            return True
        return obj == user
