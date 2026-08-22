"""
trips — services. Owner: Dev A.

WRITE layer: transactions, cross-model orchestration, side effects.
Returns objects, never response bodies.
"""

import logging
import uuid

from django.db import transaction
from django.db.models import F, Max
from rest_framework.exceptions import ValidationError

from apps.activities.models import Activity
from apps.geo.models import City
from apps.trips.constants import TripStatus
from apps.trips.models import Trip, TripActivity, TripStop
from core.utils import shift_dates

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------- trips


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


# ---------------------------------------------------------------------- stops


def _next_order(queryset) -> int:
    """One past the highest `order` in `queryset`. 1 for an empty one."""
    return (queryset.aggregate(highest=Max("order"))["highest"] or 0) + 1


@transaction.atomic
def create_stop(*, trip: Trip, **fields) -> TripStop:
    """
    Add a stop to the end of the trip.

    `order` is server-assigned: the client says *which city, which dates*, never
    where in the sequence — that is what the reorder endpoint is for.
    """
    stop = TripStop.objects.create(
        trip=trip, order=_next_order(TripStop.objects.filter(trip=trip)), **fields
    )

    # A4.11 — denormalised counter behind `/cities/popular/`. A plain `F()`
    # increment rather than a call into `geo.services`, so the dependency stays
    # one-directional (`trips → geo`) and this cannot deadlock behind a read.
    City.objects.filter(pk=stop.city_id).update(popularity_score=F("popularity_score") + 1)

    logger.info("Stop %s (city %s) added to trip %s", stop.pk, stop.city_id, trip.pk)
    return stop


@transaction.atomic
def update_stop(stop: TripStop, **fields) -> TripStop:
    for name, value in fields.items():
        setattr(stop, name, value)
    stop.save()
    return stop


@transaction.atomic
def delete_stop(stop: TripStop) -> None:
    """
    Soft-delete a stop **and** its activities.

    Done by hand because Django's cascade collector bypasses `delete()`, and
    unlike a trip's stops these rows *are* reachable another way: the flat
    `/trip-activities/{id}/` route would keep serving an activity whose section
    the user has already removed.
    """
    TripActivity.objects.filter(trip_stop=stop).delete()
    stop.delete()
    logger.info("Stop %s soft-deleted with its activities", stop.pk)


@transaction.atomic
def reorder_stops(*, trip: Trip, items: list[dict]) -> list[TripStop]:
    """
    Apply a new `order` to several stops in **one** statement.

    One `bulk_update` inside one transaction, because SQLite has no deferred
    constraints: writing the rows one at a time would need `order` to be unique
    at every intermediate step, which no reorder can promise (trap #2). That is
    also why `TripStop` has no `UniqueConstraint(trip, order)` to begin with.

    `bulk_update` does not call `save()`, so `updated_at` is left alone — a
    reorder is not a change to the stop itself.
    """
    stops = {stop.pk: stop for stop in TripStop.objects.filter(trip=trip)}

    unknown = sorted({item["id"] for item in items} - stops.keys())
    if unknown:
        raise ValidationError({"items": f"These stops do not belong to this trip: {unknown}."})

    touched = []
    for item in items:
        stop = stops[item["id"]]
        stop.order = item["order"]
        touched.append(stop)

    TripStop.objects.bulk_update(touched, ["order"])
    logger.info("Reordered %s stops on trip %s", len(touched), trip.pk)
    return sorted(stops.values(), key=lambda stop: (stop.order, stop.pk))


# ----------------------------------------------------------- trip activities


@transaction.atomic
def create_trip_activity(*, trip_stop: TripStop, **fields) -> TripActivity:
    """
    Attach a catalog activity, or a custom entry, to one day of one stop.

    Two rules worth stating out loud:

    - **`cost` is snapshotted, not referenced** (trap #5). Editing the catalog
      later must never rewrite a budget the user has already seen.
    - **`currency` is the trip's**, not the catalog row's. A trip holds one
      currency and the budget adds its children up without converting, so
      inheriting a catalog row's USD into an INR trip would silently produce a
      wrong total.
    """
    activity: Activity | None = fields.get("activity")
    if activity is not None:
        fields.setdefault("cost", activity.cost)
        fields.setdefault("duration_minutes", activity.duration_minutes)
    fields["currency"] = trip_stop.trip.currency

    trip_activity = TripActivity.objects.create(
        trip_stop=trip_stop,
        order=_next_order(
            TripActivity.objects.filter(trip_stop=trip_stop, day_date=fields["day_date"])
        ),
        **fields,
    )

    if activity is not None:
        # A4.11 — same denormalised counter as `create_stop`, for
        # `/activities/popular/`.
        Activity.objects.filter(pk=activity.pk).update(
            popularity_score=F("popularity_score") + 1
        )

    logger.info(
        "Activity %s added to stop %s on %s",
        trip_activity.pk,
        trip_stop.pk,
        trip_activity.day_date,
    )
    return trip_activity


@transaction.atomic
def update_trip_activity(trip_activity: TripActivity, **fields) -> TripActivity:
    for name, value in fields.items():
        setattr(trip_activity, name, value)
    trip_activity.save()
    return trip_activity


def delete_trip_activity(trip_activity: TripActivity) -> None:
    trip_activity.delete()
    logger.info("Trip activity %s soft-deleted", trip_activity.pk)


@transaction.atomic
def reorder_trip_activities(*, trip: Trip, items: list[dict]) -> list[TripActivity]:
    """
    Reorder activities, and move them between days and stops, in one statement.

    Calendar drag-and-drop is one gesture that can change three things at once,
    which is why `day_date` and `trip_stop` travel with `order` rather than
    going through `PATCH`. Everything is validated **before** anything is
    written, so a rejected item cannot leave half a move applied.
    """
    activities = {
        activity.pk: activity
        for activity in TripActivity.objects.filter(trip_stop__trip=trip).select_related(
            "trip_stop"
        )
    }
    stops = {stop.pk: stop for stop in TripStop.objects.filter(trip=trip)}

    unknown = sorted({item["id"] for item in items} - activities.keys())
    if unknown:
        raise ValidationError(
            {"items": f"These activities do not belong to this trip: {unknown}."}
        )

    fields = {"order"}
    touched = []
    for item in items:
        activity = activities[item["id"]]
        activity.order = item["order"]

        if "trip_stop" in item:
            if item["trip_stop"] not in stops:
                raise ValidationError(
                    {"items": f"Stop {item['trip_stop']} does not belong to this trip."}
                )
            activity.trip_stop = stops[item["trip_stop"]]
            fields.add("trip_stop")

        if "day_date" in item:
            activity.day_date = item["day_date"]
            fields.add("day_date")

        stop = activity.trip_stop
        if not stop.start_date <= activity.day_date <= stop.end_date:
            raise ValidationError(
                {
                    "items": (
                        f"Activity {activity.pk} would land on {activity.day_date}, "
                        f"outside stop {stop.pk} ({stop.start_date} to {stop.end_date})."
                    )
                }
            )
        touched.append(activity)

    TripActivity.objects.bulk_update(touched, sorted(fields))
    logger.info("Reordered %s activities on trip %s", len(touched), trip.pk)
    return sorted(touched, key=lambda item: (item.day_date, item.order, item.pk))


# ------------------------------------------------------------- share and copy


@transaction.atomic
def set_trip_public(trip: Trip, *, is_public: bool) -> Trip:
    """
    Publish or unpublish a trip.

    The `share_token` is left alone: revoking and re-sharing should give back
    the *same* link, because people have it in a chat thread. Killing old links
    is what `regenerate_share_token` is for, and it is a separate, deliberate act.
    """
    trip.is_public = is_public
    trip.save(update_fields=["is_public", "updated_at"])
    logger.info("Trip %s is_public=%s", trip.pk, is_public)
    return trip


@transaction.atomic
def regenerate_share_token(trip: Trip) -> Trip:
    """Issue a new token, which kills every link already handed out."""
    trip.share_token = uuid.uuid4()
    trip.save(update_fields=["share_token", "updated_at"])
    logger.info("Trip %s share token regenerated", trip.pk)
    return trip


def record_public_view(trip: Trip) -> None:
    """
    Count a view of the public page.

    An `F()` increment rather than read-modify-write: two people opening the
    link at once must not lose a count. Deliberately not filtered to strangers —
    the owner previewing their own link counts too, which is the simpler and
    more predictable rule.
    """
    Trip.objects.filter(pk=trip.pk).update(views_count=F("views_count") + 1)


@transaction.atomic
def copy_trip(*, source: Trip, user, start_date=None, name: str | None = None) -> Trip:
    """
    Deep-copy a shared trip into somebody's account: stops, activities, expenses.

    Every date is **rebased** so day one lands on `start_date` (decision D9) —
    copying a past itinerary into the future is the actual use case, and a copy
    that keeps last year's dates is immediately useless. Omitting `start_date`
    keeps the original dates.

    The copy is private and a `DRAFT` with a fresh `share_token`: inheriting the
    original's link would let one person's revoke break another person's trip.
    `DRAFT` also survives the status sync, so a copy of a finished trip does not
    immediately present itself as `COMPLETED`.
    """
    from apps.budget.models import Expense  # deferred: budget → trips

    offset = (start_date - source.start_date).days if start_date else 0

    trip = Trip.objects.create(
        user=user,
        name=name or source.name,
        description=source.description,
        start_date=shift_dates(source.start_date, offset),
        end_date=shift_dates(source.end_date, offset),
        # Explicit, so `save()` does not derive it from the rebased dates.
        status=TripStatus.DRAFT,
        # The same file, not a copy of it: nothing in this project deletes media,
        # so two rows pointing at one image is safe and the copy keeps its cover.
        cover_photo=source.cover_photo,
        total_budget=source.total_budget,
        currency=source.currency,
        is_public=False,
        copied_from=source,
    )

    stops = {}
    for stop in TripStop.objects.filter(trip=source).order_by("order"):
        stops[stop.pk] = TripStop.objects.create(
            trip=trip,
            city=stop.city,
            title=stop.title,
            start_date=shift_dates(stop.start_date, offset),
            end_date=shift_dates(stop.end_date, offset),
            order=stop.order,
            budget=stop.budget,
            notes=stop.notes,
        )
        # Same counter the normal add path bumps, so a copied trip's cities
        # still register on /cities/popular/.
        City.objects.filter(pk=stop.city_id).update(popularity_score=F("popularity_score") + 1)

    TripActivity.objects.bulk_create(
        [
            TripActivity(
                trip_stop=stops[item.trip_stop_id],
                activity=item.activity,
                custom_title=item.custom_title,
                day_date=shift_dates(item.day_date, offset),
                start_time=item.start_time,
                end_time=item.end_time,
                # The snapshot travels with the copy. Re-reading the catalog here
                # would silently reprice somebody else's plan.
                cost=item.cost,
                currency=item.currency,
                duration_minutes=item.duration_minutes,
                order=item.order,
                notes=item.notes,
            )
            for item in TripActivity.objects.filter(
                trip_stop__trip=source, trip_stop__is_deleted=False
            ).order_by("day_date", "order")
        ]
    )

    Expense.objects.bulk_create(
        [
            Expense(
                trip=trip,
                trip_stop=stops.get(item.trip_stop_id),
                category=item.category,
                title=item.title,
                amount=item.amount,
                currency=item.currency,
                incurred_on=shift_dates(item.incurred_on, offset),
                is_estimated=item.is_estimated,
                notes=item.notes,
            )
            for item in Expense.objects.filter(trip=source)
        ]
    )

    logger.info("Trip %s copied from %s for user %s", trip.pk, source.pk, user.pk)
    return trip
