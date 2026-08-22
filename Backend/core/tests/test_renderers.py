"""
core — the response envelope.

Worth testing directly: every endpoint in two client apps depends on this shape,
and the double-wrap guard is the kind of bug that only shows up as `data.data`
in the frontend three days later.
"""

import json

import pytest

from core.renderers import EnvelopeJSONRenderer


class _Response:
    def __init__(self, status_code: int):
        self.status_code = status_code


@pytest.fixture
def render():
    renderer = EnvelopeJSONRenderer()

    def _render(data, status: int = 200):
        raw = renderer.render(
            data, renderer_context={"response": _Response(status)}
        )
        return json.loads(raw) if raw else raw

    return _render


def test_object_is_wrapped(render):
    assert render({"id": 12}) == {
        "success": True,
        "message": None,
        "data": {"id": 12},
    }


def test_paginated_payload_nests_under_data(render):
    """Rows must land at data.results and meta at data.pagination."""
    payload = render({"results": [{"id": 1}], "pagination": {"count": 1}})
    assert payload["data"]["results"] == [{"id": 1}]
    assert payload["data"]["pagination"] == {"count": 1}


def test_already_enveloped_payload_is_not_wrapped_twice(render):
    """core.response helpers pre-build the envelope; it must pass through."""
    payload = render({"success": True, "message": "Stops reordered.", "data": None})
    assert payload == {"success": True, "message": "Stops reordered.", "data": None}
    assert "data" not in (payload["data"] or {})


def test_serializer_field_named_success_is_not_mistaken_for_an_envelope(render):
    """The guard needs `data`/`errors` too, or real payloads get swallowed."""
    payload = render({"success": True, "name": "Europe Summer"})
    assert payload["data"] == {"success": True, "name": "Europe Summer"}


def test_error_status_produces_the_error_shape(render):
    payload = render({"detail": "Not found."}, status=404)
    assert payload["success"] is False
    assert payload["message"] == "Not found."


def test_error_message_is_pulled_out_of_nested_field_errors(render):
    payload = render({"start_date": ["This field is required."]}, status=400)
    assert payload["message"] == "This field is required."


def test_no_content_gets_an_empty_body(render):
    """A 204 must not grow a body just because a renderer ran."""
    assert render(None, status=204) == b""
