"""
Exception handling.

`custom_exception_handler` is wired as DRF's `EXCEPTION_HANDLER`, so every
handled error comes out in the shape `docs/API.md` promises:

    {"success": false,
     "message": "This field is required.",
     "errors": {"fields": {"start_date": ["This field is required."]}}}

Field errors are nested under `errors.fields` so the frontend can bind them to
inputs without having to guess which top-level keys are field names.
"""

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


class ApplicationError(APIException):
    """
    A business-rule failure raised from `services.py`.

    Use this rather than `ValidationError` when the problem is not about a
    specific input field — "this trip has no stops to reorder", say.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The request could not be completed."
    default_code = "application_error"


class ConflictError(ApplicationError):
    """State conflict — the request is well-formed but clashes with reality."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "This conflicts with the current state of the resource."
    default_code = "conflict"


def _first_message(value) -> str | None:
    if isinstance(value, dict):
        for item in value.values():
            found = _first_message(item)
            if found:
                return found
        return None
    if isinstance(value, list | tuple):
        for item in value:
            found = _first_message(item)
            if found:
                return found
        return None
    return str(value) if value not in (None, "") else None


def _shape(detail) -> tuple[str, dict]:
    """Turn a DRF `exc.detail` into our `(message, errors)` pair."""
    if isinstance(detail, dict):
        # {"detail": "..."} is DRF's single-message form (404, 401, 403, throttle).
        if set(detail.keys()) == {"detail"}:
            message = _first_message(detail["detail"]) or "Request failed."
            return message, {"detail": message}

        fields = {key: value for key, value in detail.items() if key != "detail"}
        message = _first_message(detail) or "Request failed."
        errors: dict = {}
        if fields:
            errors["fields"] = fields
        if "detail" in detail:
            errors["detail"] = _first_message(detail["detail"])
        return message, errors

    if isinstance(detail, list | tuple):
        message = _first_message(detail) or "Request failed."
        return message, {"detail": list(detail)}

    message = str(detail)
    return message, {"detail": message}


def custom_exception_handler(exc, context):
    """
    Normalise anything DRF can handle into the envelope.

    Returning `None` hands the exception back to Django, which is what we want
    for genuinely unexpected errors: in dev you get the traceback page, in prod
    the 500 handler. Swallowing those into a tidy JSON body would hide real bugs
    during the build.
    """
    # Django's own ValidationError can surface from a model's `full_clean()`.
    # DRF does not know about it, so translate before handing over.
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=getattr(exc, "message_dict", None) or exc.messages)

    response = drf_exception_handler(exc, context)
    if response is None:
        view = context.get("view")
        logger.exception("Unhandled exception in %s", getattr(view, "__class__", view))
        return None

    message, errors = _shape(response.data)
    response.data = {"success": False, "message": message, "errors": errors}
    return response
