"""
The response envelope. Wired as DRF's `DEFAULT_RENDERER_CLASSES`, so views never
build it by hand.

    success  ->  {"success": true,  "message": null, "data": {...}}
    list     ->  {"success": true,  "message": null,
                  "data": {"results": [...], "pagination": {...}}}
    error    ->  {"success": false, "message": "...", "errors": {...}}

One parse path for the frontend. Retrofitting this later would touch every call
site in two client apps, which is why it is here on day one.
"""

from rest_framework.renderers import JSONRenderer

#: Keys that mark a payload as already carrying the envelope.
_ENVELOPE_KEYS = frozenset({"data", "errors"})


def _is_enveloped(data) -> bool:
    """
    True when something upstream already built the envelope.

    Two things produce pre-enveloped payloads: the helpers in `core/response.py`
    and `core.exceptions.custom_exception_handler`. Without this check we would
    wrap them a second time and the frontend would read `data.data`.

    Deliberately strict — `success` must be a real bool and at least one of
    `data`/`errors` must be present — so a serializer that happens to expose a
    field named `success` is not mistaken for an envelope.
    """
    return (
        isinstance(data, dict)
        and isinstance(data.get("success"), bool)
        and bool(_ENVELOPE_KEYS & data.keys())
    )


def _extract_message(data) -> str | None:
    """Pull a single human-readable sentence out of a DRF error body."""
    if isinstance(data, dict):
        detail = data.get("detail")
        if isinstance(detail, str):
            return detail
        for value in data.values():
            message = _extract_message(value)
            if message:
                return message
        return None
    if isinstance(data, list | tuple):
        for item in data:
            message = _extract_message(item)
            if message:
                return message
        return None
    return str(data) if data is not None else None


class EnvelopeJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")
        status_code = getattr(response, "status_code", 200)

        # 204 No Content and friends must not grow a body just because a
        # renderer ran. DRF hands us `None` for those.
        if data is None:
            return b""

        if _is_enveloped(data):
            payload = data
        elif status_code >= 400:
            # Reached when an error bypassed our exception handler — a raw
            # `Response(status=400)` from a view, for instance. Shape it the
            # same way so the client only ever sees one error format.
            payload = {
                "success": False,
                "message": _extract_message(data) or "Request failed.",
                "errors": data if isinstance(data, dict) else {"detail": data},
            }
        else:
            payload = {"success": True, "message": None, "data": data}

        return super().render(payload, accepted_media_type, renderer_context)
