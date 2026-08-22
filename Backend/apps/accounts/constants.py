"""
accounts — constants. Owner: Dev A.

`TextChoices` classes, enums and magic numbers. Import these into
`models.py` rather than declaring choices inline.
"""

from django.db import models


class UserRole(models.TextChoices):
    """Gates `/api/v1/admin/**` — see `core.permissions.IsAdminRole`."""

    USER = "USER", "User"
    ADMIN = "ADMIN", "Admin"
