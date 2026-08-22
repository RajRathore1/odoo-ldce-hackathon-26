"""
community — Django admin. Owner: Dev B.

Registrations for `/django-admin/`. Worth keeping current: it is how we
fix data by hand mid-demo.
"""

from django.contrib import admin

from apps.community.models import CommunityPost, PostComment, PostLike


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "city",
        "likes_count",
        "comments_count",
        "is_published",
        "is_flagged",
        "is_deleted",
    )
    list_filter = ("is_published", "is_flagged", "is_deleted")
    search_fields = ("title", "body", "user__email")
    list_select_related = ("user", "city")
    autocomplete_fields = ("user", "trip", "city", "activity")
    # Counters, not fields — they are maintained by community/services.py.
    readonly_fields = ("likes_count", "comments_count", "created_at", "updated_at")
    date_hierarchy = "created_at"


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "parent", "is_deleted", "created_at")
    list_filter = ("is_deleted",)
    search_fields = ("body", "user__email", "post__title")
    list_select_related = ("post", "user")
    autocomplete_fields = ("post", "user", "parent")


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "created_at")
    search_fields = ("post__title", "user__email")
    list_select_related = ("post", "user")
    autocomplete_fields = ("post", "user")
