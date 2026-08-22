"""
community — serializers. Owner: Dev B (P2).

Field validation and read shaping **only**.

Separate classes per direction — `XListSerializer`, `XDetailSerializer`,
`XCreateSerializer` — rather than one class branching on `context`.
Multi-model writes belong in `services.py`.
"""
