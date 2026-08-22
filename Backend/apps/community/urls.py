"""
User-facing routes for community. Mounted by `config/api_urls.py` under
`/community/`, so the paths here are relative to that.

`comments/<id>/` is flat for the same reason `/trip-activities/{id}/` is: the
client holds the id from the thread it is rendering, and a nested URL would only
give it a second thing to get wrong.
"""

from django.urls import path

from apps.community.views import (
    CommunityPostDetailView,
    CommunityPostListCreateView,
    PostCommentDestroyView,
    PostCommentListCreateView,
    PostLikeView,
)

urlpatterns = [
    path("posts/", CommunityPostListCreateView.as_view(), name="post-list"),
    path("posts/<int:pk>/", CommunityPostDetailView.as_view(), name="post-detail"),
    path("posts/<int:pk>/like/", PostLikeView.as_view(), name="post-like"),
    path(
        "posts/<int:post_id>/comments/",
        PostCommentListCreateView.as_view(),
        name="post-comment-list",
    ),
    path(
        "comments/<int:pk>/",
        PostCommentDestroyView.as_view(),
        name="post-comment-detail",
    ),
]
