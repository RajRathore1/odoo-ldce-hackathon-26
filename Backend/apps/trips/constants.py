"""
trips — constants. Owner: Dev A.

`TextChoices` classes, enums and magic numbers. Import these into
`models.py` rather than declaring choices inline.
"""

from django.db import models


class TripStatus(models.TextChoices):
    """
    Screen 6's tabs, plus the two states the user sets by hand.

    Labels match the UI, not the value: `PLANNED` shows as "Upcoming" because
    that is the tab the user clicks.
    """

    DRAFT = "DRAFT", "Draft"
    PLANNED = "PLANNED", "Upcoming"
    ONGOING = "ONGOING", "Ongoing"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


#: Statuses the **user** owns. `Trip.save()` derives `status` from the trip
#: dates, but must never overwrite these two — a draft whose dates are in the
#: past is still a draft, and a cancelled trip does not become "completed"
#: because its end date went by.
EXPLICIT_STATUSES = frozenset({TripStatus.DRAFT, TripStatus.CANCELLED})
