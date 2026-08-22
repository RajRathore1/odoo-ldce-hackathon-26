from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Object-level ownership check.

    Views set ``owner_field`` to the attribute holding the owning user
    (``owner`` on Trip, ``user`` on SavedDestination, ``author`` on Post).
    """

    def has_object_permission(self, request, view, obj):
        owner_field = getattr(view, "owner_field", "owner")
        return getattr(obj, owner_field, None) == request.user
