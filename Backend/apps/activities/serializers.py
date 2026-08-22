"""
activities — serializers. Owner: models: Dev A · endpoints: Dev B.

Field validation and read shaping **only**.

Separate classes per direction — `XListSerializer`, `XDetailSerializer`,
`XCreateSerializer` — rather than one class branching on `context`.
Multi-model writes belong in `services.py`.
"""
