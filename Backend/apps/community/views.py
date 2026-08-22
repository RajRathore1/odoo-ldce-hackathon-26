"""
community — views. Owner: Dev B.

Thin. Parse the request, call a service or selector, return a response.
No business rules and no multi-step ORM work.
"""

from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.community import selectors, services
from apps.community.filters import (
    AdminCommunityPostFilterSet,
    CommunityPostFilterSet,
)
from apps.community.models import CommunityPost, PostComment
from apps.community.serializers import (
    AdminCommunityPostSerializer,
    CommunityPostSerializer,
    CommunityPostWriteSerializer,
    PostCommentSerializer,
    PostCommentWriteSerializer,
)
from core.mixins import AdminOnlyMixin, UnfilteredObjectMixin
from core.pagination import FeedCursorPagination, SmallPagination
from core.permissions import IsOwner
from core.response import created, no_content, success


@extend_schema(tags=["community"])
class CommunityPostListCreateView(generics.ListCreateAPIView):
    """
    `GET|POST /community/posts/` — the feed.

    **`FeedCursorPagination`**, not the project default: a feed is ordered by
    recency and grows at the top, so page-number pagination would shift a row
    from page 2 onto page 3 between requests and show it to the reader twice.
    The trade-off is no `count`, which a feed does not need.
    """

    pagination_class = FeedCursorPagination
    filterset_class = CommunityPostFilterSet
    search_fields = ("title", "body", "city__name")
    ordering_fields = ("created_at", "likes_count", "comments_count")

    def get_queryset(self):
        return selectors.published_post_queryset(self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommunityPostWriteSerializer
        return CommunityPostSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = services.create_post(user=request.user, **serializer.validated_data)
        return created(
            data=CommunityPostSerializer(post, context={"request": request}).data,
            message="Post published.",
        )


@extend_schema(tags=["community"])
class CommunityPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    `GET|PATCH|DELETE /community/posts/{id}/`.

    Reads are open to any signed-in user; **writes are author-only**, enforced by
    `IsOwner` on `get_object()`. Unlike the trip endpoints this is not
    owner-scoped at the queryset level — a feed you can only read your own posts
    in is not a feed — so the object permission is doing real work here rather
    than acting as a second line of defence.
    """

    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return selectors.published_post_queryset(self.request.user)

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return CommunityPostWriteSerializer
        return CommunityPostSerializer

    def get_permissions(self):
        """`IsOwner` only on writes — anybody signed in may read a published post."""
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return super().get_permissions()

    def update(self, request, *args, **kwargs):
        post = self.get_object()
        serializer = self.get_serializer(
            instance=post, data=request.data, partial=kwargs.pop("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        post = services.update_post(post, **serializer.validated_data)
        return success(
            data=CommunityPostSerializer(post, context={"request": request}).data,
            message="Post updated.",
        )

    def destroy(self, request, *args, **kwargs):
        services.delete_post(self.get_object())
        return no_content()


@extend_schema(
    tags=["community"],
    summary="Like or unlike a post",
    request=None,
    responses={200: CommunityPostSerializer},
)
class PostLikeView(generics.GenericAPIView):
    """
    `POST|DELETE /community/posts/{id}/like/`.

    Returns the post, so the client can rerender the row from the response
    rather than guessing the new count. Liking twice is a 409; unliking
    something you never liked is a quiet 200, because the desired end state
    already holds.
    """

    serializer_class = CommunityPostSerializer
    permission_classes = [IsAuthenticated]

    @cached_property
    def post_object(self) -> CommunityPost:
        return get_object_or_404(
            selectors.published_post_queryset(self.request.user), pk=self.kwargs["pk"]
        )

    def post(self, request, *args, **kwargs):
        services.like_post(post=self.post_object, user=request.user)
        return self._reread(request, "Post liked.")

    def delete(self, request, *args, **kwargs):
        services.unlike_post(post=self.post_object, user=request.user)
        return self._reread(request, "Like removed.")

    def _reread(self, request, message: str):
        """
        Re-fetch before serializing, rather than returning the object the service
        handed back.

        `is_liked_by_me` is an `Exists()` **annotation**, evaluated when the row
        was first read — so the in-memory post still says what was true *before*
        the write, and `refresh_from_db()` does not recompute annotations. Without
        this re-read, liking a post returns `is_liked_by_me: false` and the client
        draws an empty heart over a like it just made.
        """
        post = get_object_or_404(
            selectors.published_post_queryset(request.user), pk=self.kwargs["pk"]
        )
        return success(
            data=CommunityPostSerializer(post, context={"request": request}).data,
            message=message,
        )


@extend_schema(tags=["community"])
class PostCommentListCreateView(generics.ListCreateAPIView):
    """
    `GET|POST /community/posts/{post_id}/comments/`.

    `SmallPagination`: the rows are nested — each carries its replies — so twenty
    of them is a lot more than twenty comments.
    """

    pagination_class = SmallPagination
    permission_classes = [IsAuthenticated]

    @cached_property
    def post_object(self) -> CommunityPost:
        return get_object_or_404(
            selectors.published_post_queryset(self.request.user),
            pk=self.kwargs["post_id"],
        )

    def get_queryset(self):
        return selectors.comment_queryset(self.post_object)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PostCommentWriteSerializer
        return PostCommentSerializer

    def get_serializer_context(self) -> dict:
        return {**super().get_serializer_context(), "post": self.post_object}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = services.create_comment(
            post=self.post_object, user=request.user, **serializer.validated_data
        )
        return created(
            data=PostCommentSerializer(comment, context=self.get_serializer_context()).data,
            message="Comment added.",
        )


@extend_schema(tags=["community"])
class PostCommentDestroyView(generics.DestroyAPIView):
    """
    `DELETE /community/comments/{id}/` — author only.

    Flat, like `/trip-activities/{id}/`: the client holds the comment id from the
    thread it is looking at, and nesting the post id would only give it a second
    thing to get wrong.
    """

    serializer_class = PostCommentSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = PostComment.objects.select_related("user", "post")

    def destroy(self, request, *args, **kwargs):
        services.delete_comment(self.get_object())
        return no_content()


# ---------------------------------------------------------------------- admin


@extend_schema(tags=["admin-community"])
class AdminPostListView(AdminOnlyMixin, generics.ListAPIView):
    """`GET /admin/posts/` — the moderation queue, unpublished and flagged included."""

    serializer_class = AdminCommunityPostSerializer
    filterset_class = AdminCommunityPostFilterSet
    search_fields = ("title", "body", "user__email")
    ordering_fields = ("created_at", "likes_count", "comments_count")
    ordering = ("-created_at",)

    def get_queryset(self):
        return selectors.admin_post_queryset()


@extend_schema(tags=["admin-community"])
class AdminPostDetailView(
    AdminOnlyMixin, UnfilteredObjectMixin, generics.RetrieveUpdateDestroyAPIView
):
    """
    `GET|PATCH|DELETE /admin/posts/{id}/`.

    `PATCH` reaches `is_flagged` and `is_published` only — the serializer makes
    the rest read-only. A moderator hides or flags a post; they do not edit what
    somebody said.
    """

    serializer_class = AdminCommunityPostSerializer

    def get_queryset(self):
        return selectors.admin_post_queryset()

    def update(self, request, *args, **kwargs):
        post = self.get_object()
        serializer = self.get_serializer(
            instance=post, data=request.data, partial=kwargs.pop("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        post = services.moderate_post(post, **serializer.validated_data)
        return success(data=AdminCommunityPostSerializer(post).data, message="Post moderated.")

    def destroy(self, request, *args, **kwargs):
        services.delete_post(self.get_object())
        return no_content()
