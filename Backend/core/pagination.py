"""
Pagination classes.

`StandardPagination` is wired as DRF's `DEFAULT_PAGINATION_CLASS`, so **every**
list endpoint is paginated with no per-view work. Opt out only for bounded
aggregate responses (analytics series, top-N) with `pagination_class = None`.

All of these emit the same envelope-inner shape:

    {"results": [...], "pagination": {...}}

`core.renderers.EnvelopeJSONRenderer` then nests that under `data`, so the
frontend always finds rows at `data.results` and meta at `data.pagination`.
"""

from collections import OrderedDict

from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """The default. 20 per page, client may request up to 100."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("results", data),
                    (
                        "pagination",
                        OrderedDict(
                            [
                                ("count", self.page.paginator.count),
                                ("page", self.page.number),
                                ("pages", self.page.paginator.num_pages),
                                ("page_size", self.get_page_size(self.request)),
                                ("has_next", self.page.has_next()),
                                ("has_previous", self.page.has_previous()),
                                ("next", self.get_next_link()),
                                ("previous", self.get_previous_link()),
                            ]
                        ),
                    ),
                ]
            )
        )

    def get_paginated_response_schema(self, schema):
        """Teach drf-spectacular the shape above, so Swagger matches reality."""
        return {
            "type": "object",
            "required": ["results", "pagination"],
            "properties": {
                "results": schema,
                "pagination": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer", "example": 137},
                        "page": {"type": "integer", "example": 2},
                        "pages": {"type": "integer", "example": 7},
                        "page_size": {"type": "integer", "example": self.page_size},
                        "has_next": {"type": "boolean", "example": True},
                        "has_previous": {"type": "boolean", "example": True},
                        "next": {"type": "string", "nullable": True, "format": "uri"},
                        "previous": {"type": "string", "nullable": True, "format": "uri"},
                    },
                },
            },
        }


class SmallPagination(StandardPagination):
    """For nested/secondary lists where 20 rows is more than the UI shows."""

    page_size = 10
    max_page_size = 50


class LargePagination(StandardPagination):
    """
    City and activity pickers. The user is scrolling a catalog looking for one
    row, so a bigger page means fewer round-trips.
    """

    page_size = 50
    max_page_size = 200


class FeedCursorPagination(CursorPagination):
    """
    The community feed. Cursor-based rather than page-based so a post arriving
    mid-scroll cannot shift a row from page 2 onto page 3 and make the reader
    see it twice.

    No `count` — that is the trade-off for stability, and a feed does not need it.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = "-created_at"
    cursor_query_param = "cursor"

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("results", data),
                    (
                        "pagination",
                        OrderedDict(
                            [
                                ("page_size", self.get_page_size(self.request)),
                                ("has_next", self.get_next_link() is not None),
                                ("has_previous", self.get_previous_link() is not None),
                                ("next", self.get_next_link()),
                                ("previous", self.get_previous_link()),
                            ]
                        ),
                    ),
                ]
            )
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "required": ["results", "pagination"],
            "properties": {
                "results": schema,
                "pagination": {
                    "type": "object",
                    "properties": {
                        "page_size": {"type": "integer", "example": self.page_size},
                        "has_next": {"type": "boolean"},
                        "has_previous": {"type": "boolean"},
                        "next": {"type": "string", "nullable": True, "format": "uri"},
                        "previous": {"type": "string", "nullable": True, "format": "uri"},
                    },
                },
            },
        }
