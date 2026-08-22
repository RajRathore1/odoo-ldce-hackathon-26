"""
community — selectors. Owner: Dev B.

READ layer: querysets, `annotate`, `aggregate`, `select_related` /
`prefetch_related`. Never mutates anything.
"""

from django.db.models import Exists, OuterRef, Prefetch

from apps.community.models import CommunityPost, PostComment, PostLike


def post_queryset(user=None):
    """
    The feed.

    Four joins and one `Exists()`, so a row costs no queries of its own: the
    author, the city and its country, the trip, and whether *this* caller has
    liked it. `likes_count` and `comments_count` are stored columns, so they are
    free.

    `user` may be anonymous, in which case `is_liked_by_me` is simply absent and
    the serializer reads it as `false`.
    """
    queryset = CommunityPost.objects.select_related(
        "user", "city", "city__country", "trip", "activity"
    )

    if user is not None and user.is_authenticated:
        queryset = queryset.annotate(
            is_liked_by_me=Exists(PostLike.objects.filter(post=OuterRef("pk"), user=user))
        )
    return queryset


def published_post_queryset(user=None):
    """
    The feed as the public sees it.

    Unpublished and flagged posts are hidden here, not in the view, so no
    endpoint can forget: moderation that only applies to the list is not
    moderation.
    """
    return post_queryset(user).filter(is_published=True, is_flagged=False)


def comment_queryset(post):
    """
    A post's comments, top level only, each with its replies prefetched.

    Returning the replies nested rather than flat is what keeps the client from
    having to rebuild the thread — and prefetching them is what keeps that from
    being a query per comment.
    """
    return (
        PostComment.objects.filter(post=post, parent__isnull=True)
        .select_related("user")
        .prefetch_related(
            Prefetch(
                "replies",
                queryset=PostComment.objects.select_related("user").order_by("created_at"),
            )
        )
        .order_by("created_at")
    )


def admin_post_queryset():
    """
    `/admin/posts/` — moderation.

    `all_objects`, so a soft-deleted post stays visible with
    `?include_deleted=true`, and unpublished and flagged posts are included:
    those are precisely the rows a moderator came for.
    """
    return CommunityPost.all_objects.select_related("user", "city").order_by("-created_at")
