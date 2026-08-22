"""
geo — services. Owner: models: Dev A · endpoints: Dev B.

WRITE layer: transactions, cross-model orchestration, side effects.
Returns objects, never response bodies.
"""

import logging

from django.db import transaction
from django.db.models import Count, IntegerField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce

from apps.geo.models import City, SavedDestination
from core.exceptions import ConflictError

logger = logging.getLogger(__name__)


@transaction.atomic
def save_destination(*, user, city: City, note: str = "") -> SavedDestination:
    """
    Bookmark a city for a user.

    A second save of the same city is a **409**, not a silent no-op: the
    frontend draws a filled bookmark from `is_saved`, so if it is asking again
    its state is stale and it should re-read rather than be told "fine".
    """
    if SavedDestination.objects.filter(user=user, city=city).exists():
        raise ConflictError("You have already saved this destination.")
    return SavedDestination.objects.create(user=user, city=city, note=note)


def remove_saved_destination(saved: SavedDestination) -> None:
    """Soft delete. The scoped unique constraint lets the city be re-saved later."""
    saved.delete()


def recalculate_city_popularity(city_id: int | None = None) -> int:
    """
    Rebuild `City.popularity_score` from the trip stops that point at it.

    The score is denormalised so `/cities/popular/` and the admin's popular-city
    table are index scans instead of live aggregates over every trip. It is kept
    up to date incrementally by `trips.services.create_stop`; this is the repair
    job for when that has drifted — after a seed, a bulk delete, or a restore.

    One correlated `UPDATE`, not one query per city. Counted through the reverse
    accessor `trip_stops`, so `geo` still imports nothing from `trips`
    (`LAYOUT.md` §5). Returns the number of rows touched.
    """
    live_stop_count = (
        City.objects.filter(pk=OuterRef("pk"))
        .annotate(total=Count("trip_stops", filter=Q(trip_stops__is_deleted=False)))
        .values("total")[:1]
    )

    queryset = City.objects.all()
    if city_id is not None:
        queryset = queryset.filter(pk=city_id)

    updated = queryset.update(
        popularity_score=Coalesce(Subquery(live_stop_count, output_field=IntegerField()), 0)
    )
    logger.info("Recalculated popularity for %s cities", updated)
    return updated
