"""
community — services. Owner: Dev B.

WRITE layer: transactions, cross-model orchestration, side effects.
Returns objects, never response bodies.

**The counters live here, not in signals** (`MODELS.md` §8). A signal is
invisible at the call site: six months on, nobody reading `PostLike.objects
.create(...)` knows a counter moved. Every mutation below adjusts its counter in
the same transaction as the row it belongs to, with an `F()` expression so two
concurrent likes cannot lose one.
"""

import logging

from django.db import transaction
from django.db.models import Count, F, IntegerField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce

from apps.community.models import CommunityPost, PostComment, PostLike
from core.exceptions import ConflictError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------- posts


@transaction.atomic
def create_post(*, user, **fields) -> CommunityPost:
    post = CommunityPost.objects.create(user=user, **fields)
    logger.info("Post %s created by user %s", post.pk, user.pk)
    return post


@transaction.atomic
def update_post(post: CommunityPost, **fields) -> CommunityPost:
    for name, value in fields.items():
        setattr(post, name, value)
    post.save()
    return post


@transaction.atomic
def delete_post(post: CommunityPost) -> None:
    """
    Soft-delete a post.

    Its comments keep `is_deleted=False` — Django's collector bypasses
    `delete()` — which is harmless because comments are only ever reached
    through their post. The likes stay too, and are hard-deleted with the row if
    it is ever purged.
    """
    post.delete()
    logger.info("Post %s soft-deleted", post.pk)


# ---------------------------------------------------------------------- likes


@transaction.atomic
def like_post(*, post: CommunityPost, user) -> CommunityPost:
    """
    Like a post, and move the counter.

    A second like is a **409**, not a silent success: the client draws a filled
    heart from `is_liked_by_me`, so if it is asking again its state is stale and
    it should re-read rather than be told everything is fine.
    """
    _, created = PostLike.objects.get_or_create(post=post, user=user)
    if not created:
        raise ConflictError("You have already liked this post.")

    CommunityPost.objects.filter(pk=post.pk).update(likes_count=F("likes_count") + 1)
    post.refresh_from_db(fields=["likes_count"])
    return post


@transaction.atomic
def unlike_post(*, post: CommunityPost, user) -> CommunityPost:
    """
    Remove a like.

    A **hard** delete (D3): a soft-deleted row would keep occupying
    `unique_together`, so the same person could never like the post again.

    The counter only moves if a row was actually removed, so a double unlike
    cannot drive it negative — `PositiveIntegerField` would raise, and on SQLite
    it would happily store nonsense.
    """
    deleted, _ = PostLike.objects.filter(post=post, user=user).delete()
    if deleted:
        CommunityPost.objects.filter(pk=post.pk, likes_count__gt=0).update(
            likes_count=F("likes_count") - 1
        )
    post.refresh_from_db(fields=["likes_count"])
    return post


# ------------------------------------------------------------------- comments


@transaction.atomic
def create_comment(*, post: CommunityPost, user, **fields) -> PostComment:
    """Add a comment or a reply, and move the post's counter."""
    comment = PostComment.objects.create(post=post, user=user, **fields)
    CommunityPost.objects.filter(pk=post.pk).update(comments_count=F("comments_count") + 1)
    logger.info("Comment %s added to post %s", comment.pk, post.pk)
    return comment


@transaction.atomic
def delete_comment(comment: PostComment) -> None:
    """
    Soft-delete a comment, its replies, and the counter for all of them.

    The replies go explicitly, because the collector bypasses `delete()` and a
    reply whose parent is gone is unreachable but still counted. Decrementing by
    the whole subtree is what keeps `comments_count` honest.
    """
    replies = list(PostComment.objects.filter(parent=comment).values_list("pk", flat=True))
    removed = len(replies) + 1

    PostComment.objects.filter(pk__in=replies).delete()
    comment.delete()

    CommunityPost.objects.filter(pk=comment.post_id, comments_count__gte=removed).update(
        comments_count=F("comments_count") - removed
    )
    logger.info("Comment %s soft-deleted with %s replies", comment.pk, len(replies))


# ---------------------------------------------------------------------- admin


@transaction.atomic
def moderate_post(post: CommunityPost, **fields) -> CommunityPost:
    """Flag or hide a post. Only `is_flagged` / `is_published` reach this."""
    for name, value in fields.items():
        setattr(post, name, value)
    post.save()
    logger.info(
        "Post %s moderated: published=%s flagged=%s",
        post.pk,
        post.is_published,
        post.is_flagged,
    )
    return post


def recalculate_post_counters(post_id: int | None = None) -> int:
    """
    Rebuild `likes_count` / `comments_count` from the rows behind them.

    The repair job for the denormalised counters, in the same spirit as
    `geo.services.recalculate_city_popularity`: they are maintained
    incrementally above, and this is what fixes them after a bulk delete, an
    import, or a bug. One `UPDATE` per counter, not one per post.
    """
    queryset = CommunityPost.objects.all()
    if post_id is not None:
        queryset = queryset.filter(pk=post_id)

    likes = (
        CommunityPost.objects.filter(pk=OuterRef("pk"))
        .annotate(total=Count("likes"))
        .values("total")[:1]
    )
    comments = (
        CommunityPost.objects.filter(pk=OuterRef("pk"))
        .annotate(total=Count("comments", filter=Q(comments__is_deleted=False)))
        .values("total")[:1]
    )

    updated = queryset.update(
        likes_count=Coalesce(Subquery(likes, output_field=IntegerField()), 0),
        comments_count=Coalesce(Subquery(comments, output_field=IntegerField()), 0),
    )
    logger.info("Recalculated counters for %s posts", updated)
    return updated
