"""
activities — constants. Owner: Dev A (models) · Dev B (endpoints).

`TextChoices` classes, enums and magic numbers. Import these into
`models.py` rather than declaring choices inline.
"""

from django.db import models


class ActivityType(models.TextChoices):
    """Screen 8's type filter. Also exposed as an enum in the OpenAPI schema."""

    SIGHTSEEING = "SIGHTSEEING", "Sightseeing"
    FOOD = "FOOD", "Food & Dining"
    ADVENTURE = "ADVENTURE", "Adventure"
    CULTURE = "CULTURE", "Culture & Heritage"
    NIGHTLIFE = "NIGHTLIFE", "Nightlife"
    SHOPPING = "SHOPPING", "Shopping"
    NATURE = "NATURE", "Nature & Outdoors"
    RELAX = "RELAX", "Relaxation"
    TRANSPORT = "TRANSPORT", "Transport"
    OTHER = "OTHER", "Other"
