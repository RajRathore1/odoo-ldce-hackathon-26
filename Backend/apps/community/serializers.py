"""
community — serializers. Owner: Dev B.

Validation and shaping only. No cross-model writes, no calls into other apps.

`community` may import `accounts`, `trips`, `geo` and `activities`
(`LAYOUT.md` §5), so the nested shapes are reused rather than redeclared —
`PublicUserSerializer` in particular, because a feed is a public surface and the
author must be reduced to the same first-name-and-avatar shape the shared trip
page uses.
"""

from rest_framework import serializers

from apps.accounts.serializers import PublicUserSerializer
from apps.community.models import CommunityPost, PostComment
from apps.geo.serializers import CityMiniSerializer


class PostTripSerializer(serializers.Serializer):
    """
    The trip a post is about, reduced to a link.

    Deliberately tiny: a feed row is not a place to publish somebody's budget.
    `share_url` is present because "read the full itinerary" is the point of
    attaching a trip, and it only resolves if the author shared it.
    """

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    share_url = serializers.CharField(read_only=True)
    is_public = serializers.BooleanField(read_only=True)


class CommunityPostSerializer(serializers.ModelSerializer):
    """
    One row of the feed, and the detail body.

    `likes_count` and `comments_count` are stored columns, not aggregates — the
    feed is the most-read list in the app. `is_liked_by_me` is an `Exists()`
    annotation from the selector, so the heart renders without a second request.
    """

    author = PublicUserSerializer(source="user", read_only=True)
    city = CityMiniSerializer(read_only=True)
    trip = PostTripSerializer(read_only=True)
    activity_name = serializers.CharField(source="activity.name", read_only=True, default=None)
    is_liked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = (
            "id",
            "title",
            "body",
            "cover_image",
            "author",
            "city",
            "trip",
            "activity_name",
            "likes_count",
            "comments_count",
            "is_liked_by_me",
            "created_at",
        )

    def get_is_liked_by_me(self, post) -> bool:
        return bool(getattr(post, "is_liked_by_me", False))


class CommunityPostWriteSerializer(serializers.ModelSerializer):
    """
    `POST /community/posts/` and `PATCH /community/posts/{id}/`.

    Absent on purpose: `likes_count`, `comments_count`, `is_flagged` and
    `is_published`. The first two are counters, and the last two are moderation —
    an author who could set `is_flagged=False` could un-flag their own post.
    """

    class Meta:
        model = CommunityPost
        fields = ("title", "body", "trip", "city", "activity", "cover_image")

    def validate_trip(self, trip):
        """
        You may only attach **your own** trip.

        Without this, anybody could publish a feed post carrying a link to a
        stranger's trip — and `share_url` in the payload would hand out a working
        share token for it.
        """
        if trip is not None and trip.user_id != self.context["request"].user.pk:
            raise serializers.ValidationError("You can only post about your own trip.")
        return trip


class PostCommentSerializer(serializers.ModelSerializer):
    """One comment. `replies` is populated on the top-level rows only."""

    author = PublicUserSerializer(source="user", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ("id", "post", "author", "parent", "body", "replies", "created_at")

    def get_replies(self, comment) -> list:
        """
        From the selector's prefetch. `[]` on a reply, because the API only
        nests one level — see `PostCommentWriteSerializer.validate_parent`.
        """
        if comment.parent_id is not None:
            return []
        return PostCommentSerializer(
            comment.replies.all(), many=True, context=self.context
        ).data


class PostCommentWriteSerializer(serializers.ModelSerializer):
    """`POST /community/posts/{id}/comments/` — `body`*, optional `parent`."""

    class Meta:
        model = PostComment
        fields = ("body", "parent")

    def validate_parent(self, parent):
        """
        A reply may only hang off a **top-level comment on this post**.

        Two separate rules, both worth enforcing here rather than discovering in
        the renderer: a parent from another post would silently vanish from the
        thread, and a reply to a reply is a depth the client cannot draw.
        """
        if parent is None:
            return parent

        if parent.post_id != self.context["post"].pk:
            raise serializers.ValidationError("That comment belongs to another post.")
        if parent.parent_id is not None:
            raise serializers.ValidationError(
                "Replies are one level deep. Reply to the top-level comment instead."
            )
        return parent


# ---------------------------------------------------------------------- admin


class AdminCommunityPostSerializer(serializers.ModelSerializer):
    """
    `/admin/posts/` — moderation.

    Carries the author's email and the moderation flags, none of which appear on
    the public feed shape. Only `is_flagged` and `is_published` are writable: a
    moderator hides or flags a post, they do not rewrite what somebody said.
    """

    author_email = serializers.EmailField(source="user.email", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True, default=None)

    class Meta:
        model = CommunityPost
        fields = (
            "id",
            "title",
            "body",
            "author_email",
            "city_name",
            "likes_count",
            "comments_count",
            "is_published",
            "is_flagged",
            "is_deleted",
            "created_at",
        )
        read_only_fields = (
            "title",
            "body",
            "likes_count",
            "comments_count",
            "is_deleted",
            "created_at",
        )
