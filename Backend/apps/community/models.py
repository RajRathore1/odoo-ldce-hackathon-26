"""
community — models. Owner: Dev B.

`CommunityPost`, `PostComment`, `PostLike` — see docs/MODELS.md §8.

`community` sits at the bottom of the import graph: it may read `accounts`,
`trips`, `geo` and `activities`, and nothing imports it back (`LAYOUT.md` §5).
Every foreign key out of this app is a **string reference**, so the module stays
importable regardless of app-loading order.

`likes_count` and `comments_count` are denormalised counters maintained by
`services.py` — **not signals**. A signal is invisible at the call site, and a
counter that drifts is a number four screens read.
"""

from django.conf import settings
from django.db import models

from core.models import BaseModel, TimeStampedModel


class CommunityPost(BaseModel):
    """
    One shared travel note. The mockup's community feed.

    Every relation except `user` is optional and `SET_NULL`: a post about a trip
    that its author later deleted is still a post worth reading, and losing the
    text because the trip went away would be the wrong trade.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    trip = models.ForeignKey(
        "trips.Trip",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    city = models.ForeignKey(
        "geo.City",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    activity = models.ForeignKey(
        "activities.Activity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )

    title = models.CharField(max_length=200)
    body = models.TextField()
    cover_image = models.ImageField(upload_to="posts/", null=True, blank=True)

    # Denormalised, maintained in services.py. The feed is the most-read list in
    # the app; counting likes live would be a subquery per row.
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    is_published = models.BooleanField(default=True)
    # Admin moderation only — never settable by the author.
    is_flagged = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["-created_at"], name="post_created_idx"),
            models.Index(fields=["city"], name="post_city_idx"),
            models.Index(fields=["is_published"], name="post_published_idx"),
        ]

    def __str__(self) -> str:
        return self.title


class PostComment(BaseModel):
    """
    A comment, or a reply to one via `parent`.

    One level of nesting is all the mockup shows, but the self-FK does not
    enforce that — the serializer does, so a reply to a reply is a 400 rather
    than a thread nobody can render.
    """

    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_comments"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )
    body = models.TextField()

    class Meta:
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=["post", "created_at"], name="comment_post_created_idx"),
        ]

    def __str__(self) -> str:
        return f"comment {self.pk} on post {self.post_id}"


class PostLike(TimeStampedModel):
    """
    A like. **The one model in the project that is not soft-deleted** (D3).

    `TimeStampedModel`, and unliking is a real `DELETE`: a soft-deleted row would
    keep occupying `unique_together`, so the same person could never like the
    same post again (trap #3). There is nothing to preserve here — the fact
    somebody once liked something is not history worth keeping.
    """

    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_likes"
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="uniq_post_like"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} likes {self.post_id}"
