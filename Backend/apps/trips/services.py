"""
trips — services. Owner: Dev A.

WRITE layer: transactions, cross-model orchestration, side effects.
Returns objects, never response bodies.
"""

import logging

from django.db import transaction

from apps.trips.models import Trip

logger = logging.getLogger(__name__)


@transaction.atomic
def create_trip(*, user, **fields) -> Trip:
    """
    Create a trip for `user`.

    `status` is not passed through untouched — `Trip.save()` derives it from the
    dates unless the caller explicitly asked for `DRAFT` or `CANCELLED`.
    """
    trip = Trip.objects.create(user=user, **fields)
    logger.info("Trip %s created by user %s", trip.pk, user.pk)
    return trip


@transaction.atomic
def update_trip(trip: Trip, **fields) -> Trip:
    """
    Apply validated fields and save.

    A full `save()` rather than `update_fields`, because moving the dates has to
    re-run the status sync — and a partial save that skipped it would leave a
    trip whose status disagrees with its own dates.
    """
    for name, value in fields.items():
        setattr(trip, name, value)
    trip.save()
    return trip


def delete_trip(trip: Trip) -> None:
    """
    Soft-delete a trip.

    Its stops keep `is_deleted=False` — Django's cascade collector bypasses
    `delete()` (trap #2). That is harmless, because stops are only ever reached
    through their trip, and it keeps "undelete this trip" a one-field update.
    """
    trip.delete()
    logger.info("Trip %s soft-deleted", trip.pk)
