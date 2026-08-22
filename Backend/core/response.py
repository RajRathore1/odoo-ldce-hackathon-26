"""
Helpers for hand-built responses — action endpoints that return a message rather
than a serialized object (`/share/`, `/reorder/`, `/logout/`).

Regular serializer responses need none of this: return a plain `Response(data)`
and `EnvelopeJSONRenderer` wraps it. Reach for these only when you want to set
`message`, which the renderer leaves as `null`.

    return success(data={"order": [3, 1, 2]}, message="Stops reordered.")
"""

from rest_framework import status as http_status
from rest_framework.response import Response


def success(data=None, message: str | None = None, status: int = http_status.HTTP_200_OK):
    return Response({"success": True, "message": message, "data": data}, status=status)


def created(data=None, message: str | None = None):
    return Response(
        {"success": True, "message": message, "data": data},
        status=http_status.HTTP_201_CREATED,
    )


def no_content():
    """204. Body intentionally empty — the renderer short-circuits on `None`."""
    return Response(status=http_status.HTTP_204_NO_CONTENT)


def error(
    message: str,
    errors: dict | None = None,
    status: int = http_status.HTTP_400_BAD_REQUEST,
):
    """
    Prefer *raising* `ValidationError` / `ApplicationError` over returning this —
    an exception cannot be forgotten halfway down a function, and the handler
    shapes it identically. This exists for the cases where a view has already
    done work it wants to report on.
    """
    return Response(
        {"success": False, "message": message, "errors": errors or {}},
        status=status,
    )
