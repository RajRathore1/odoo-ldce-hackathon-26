"""
Abstract model bases. **Frozen after H1** — every app model inherits from here,
so a change to these is a migration in eight apps.

    from core.models import BaseModel

    class Trip(BaseModel):
        name = models.CharField(max_length=150)
        # created_at / updated_at / is_deleted / deleted_at are inherited.
        # Never redeclare them.
"""

import uuid

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet whose `.delete()` marks rows instead of removing them."""

    def delete(self):
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        """Actually remove the rows. Use in tests and data-repair only."""
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)

    def restore(self):
        return self.update(is_deleted=False, deleted_at=None)


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """Default manager: soft-deleted rows are invisible."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """Escape hatch: sees everything, including soft-deleted rows."""


class TimeStampedModel(models.Model):
    """Timestamps only. Use this for rows we genuinely hard-delete (`PostLike`)."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel):
    """
    **The default base for every app model.**

    `objects` excludes soft-deleted rows; `all_objects` includes them. Both
    `instance.delete()` and `queryset.delete()` soft-delete — pass `hard=True`
    (or call `.hard_delete()`) to really remove a row.

    Two things to know:

    1. **Soft delete does not cascade.** Django's cascade collector bypasses
       `delete()`, so soft-deleting a `Trip` leaves its `TripStop` rows with
       `is_deleted=False`. That is harmless for reads (stops are only reachable
       through their trip) but it means anything *counting* child rows must
       filter on the parent. Where a cascade genuinely matters, do it explicitly
       in the app's `services.py`.

    2. **A soft-deleted row still occupies its unique key.** If a user must be
       able to re-create something they "deleted", scope the constraint:

           UniqueConstraint(fields=["user", "city"], condition=Q(is_deleted=False),
                            name="uniq_saved_destination_alive")
    """

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard=False):
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
        return 1, {self._meta.label: 1}

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])


class UUIDBaseModel(BaseModel):
    """`BaseModel` with a UUID primary key. Available; nothing uses it yet."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class OrderedModel(models.Model):
    """
    User-controlled ordering. Used by `TripStop` and `TripActivity`.

    ⚠️ **Declare `Meta` explicitly when you combine this with `BaseModel`.**
    Django resolves a child's `Meta` by MRO, so `class TripStop(BaseModel,
    OrderedModel)` with no `Meta` of its own silently picks up `BaseModel.Meta`
    and loses the ordering. Do this instead:

        class Meta(OrderedModel.Meta):
            abstract = False
            indexes = [...]

    ⚠️ **Do not add `UniqueConstraint(parent, order)`.** SQLite has no deferred
    constraints, so any reorder would collide mid-update. Reordering is a single
    `bulk_update` inside `transaction.atomic()` instead.
    """

    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ("order", "id")
