"""community — the admin moderation tree (task B7.6)."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, AdminFactory, UserFactory
from apps.community.models import CommunityPost
from apps.community.tests.factories import PostFactory

pytestmark = pytest.mark.django_db

LIST_URL = reverse("admin-post-list")


def detail_url(post_id) -> str:
    return reverse("admin-post-detail", args=[post_id])


def signed_in(user) -> APIClient:
    api = APIClient()
    response = api.post(
        reverse("auth-login"),
        {"email": user.email, "password": DEFAULT_PASSWORD},
        format="json",
    )
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['tokens']['access']}")
    return api


@pytest.fixture
def client():
    return signed_in(AdminFactory(email="admin@globetrotter.dev"))


class TestModerationQueue:
    def test_the_row_carries_the_author_and_the_flags(self, client):
        author = UserFactory(email="riya@example.com")
        post = PostFactory(user=author, title="Bir Billing", likes_count=4)

        row = client.get(LIST_URL).json()["data"]["results"][0]

        assert row["id"] == post.pk
        assert row["author_email"] == "riya@example.com"
        assert row["likes_count"] == 4
        assert row["is_published"] is True
        assert row["is_flagged"] is False

    def test_it_shows_unpublished_and_flagged_posts(self, client):
        """The rows a moderator came for — the public feed hides all of these."""
        hidden = PostFactory(is_published=False)
        flagged = PostFactory(is_flagged=True)

        ids = {row["id"] for row in client.get(LIST_URL).json()["data"]["results"]}

        assert {hidden.pk, flagged.pk} <= ids

    def test_it_filters_the_queue_by_flag(self, client):
        flagged = PostFactory(is_flagged=True)
        PostFactory()

        rows = client.get(LIST_URL, {"is_flagged": "true"}).json()["data"]["results"]

        assert [row["id"] for row in rows] == [flagged.pk]

    def test_it_searches_by_author_email(self, client):
        match = PostFactory(user=UserFactory(email="riya@example.com"))
        PostFactory(user=UserFactory(email="other@example.com"))

        rows = client.get(LIST_URL, {"search": "riya"}).json()["data"]["results"]

        assert [row["id"] for row in rows] == [match.pk]

    def test_deleted_posts_are_hidden_unless_asked_for(self, client):
        post = PostFactory()
        post.delete()

        assert client.get(LIST_URL).json()["data"]["pagination"]["count"] == 0
        with_deleted = client.get(LIST_URL, {"include_deleted": "true"}).json()
        assert [row["id"] for row in with_deleted["data"]["results"]] == [post.pk]

    def test_query_count_does_not_grow_with_the_page(self, client, django_assert_num_queries):
        PostFactory.create_batch(3)
        with django_assert_num_queries(3) as captured:
            client.get(LIST_URL)

        PostFactory.create_batch(12)
        with django_assert_num_queries(len(captured.captured_queries)):
            client.get(LIST_URL)


class TestModerationActions:
    def test_flagging_hides_the_post_from_the_feed(self, client):
        """The moderation has to actually reach the public surface."""
        author = UserFactory(email="riya@example.com")
        post = PostFactory(user=author)

        response = client.patch(detail_url(post.pk), {"is_flagged": True}, format="json")

        assert response.status_code == 200
        assert response.json()["message"] == "Post moderated."
        feed = signed_in(author).get(reverse("post-list")).json()["data"]["results"]
        assert feed == []

    def test_unpublishing_hides_it_too(self, client):
        author = UserFactory(email="riya@example.com")
        post = PostFactory(user=author)

        client.patch(detail_url(post.pk), {"is_published": False}, format="json")

        feed = signed_in(author).get(reverse("post-list")).json()["data"]["results"]
        assert feed == []

    def test_a_moderator_cannot_rewrite_the_post(self, client):
        """Hiding and flagging, not editing what somebody said."""
        post = PostFactory(title="Original", body="Original body")

        client.patch(
            detail_url(post.pk),
            {"title": "Rewritten", "body": "Rewritten", "is_flagged": True},
            format="json",
        )

        post.refresh_from_db()
        assert (post.title, post.body) == ("Original", "Original body")
        assert post.is_flagged is True

    def test_the_counters_cannot_be_typed_over(self, client):
        post = PostFactory(likes_count=4)

        client.patch(detail_url(post.pk), {"likes_count": 9999}, format="json")

        post.refresh_from_db()
        assert post.likes_count == 4

    def test_delete_is_soft(self, client):
        post = PostFactory()

        response = client.delete(detail_url(post.pk))

        assert response.status_code == 204
        assert not CommunityPost.objects.filter(pk=post.pk).exists()
        assert CommunityPost.all_objects.filter(pk=post.pk).exists()

    def test_a_deleted_post_stays_addressable_by_id(self, client):
        post = PostFactory()
        client.delete(detail_url(post.pk))

        assert client.get(detail_url(post.pk)).status_code == 200

    def test_an_ordinary_user_cannot_moderate(self, client):
        post = PostFactory(is_flagged=True)

        response = signed_in(UserFactory()).patch(
            detail_url(post.pk), {"is_flagged": False}, format="json"
        )

        assert response.status_code == 403
        post.refresh_from_db()
        assert post.is_flagged is True


class TestPostsCountReachesTheAdminUserRow:
    """
    The counter `accounts` renders without importing `community`.

    Tested from this side because `community → accounts` is the legal direction
    (`LAYOUT.md` §5) — `accounts` reaches `posts` through the reverse accessor,
    which exists because the FK is declared here.
    """

    def test_it_counts_the_users_posts(self, client):
        author = UserFactory(email="riya@example.com")
        PostFactory.create_batch(3, user=author)

        rows = {
            row["email"]: row
            for row in client.get(reverse("admin-user-list")).json()["data"]["results"]
        }

        assert rows["riya@example.com"]["posts_count"] == 3

    def test_a_deleted_post_does_not_count(self, client):
        author = UserFactory(email="riya@example.com")
        PostFactory(user=author)
        PostFactory(user=author).delete()

        rows = {
            row["email"]: row
            for row in client.get(reverse("admin-user-list")).json()["data"]["results"]
        }

        assert rows["riya@example.com"]["posts_count"] == 1

    def test_trips_and_posts_do_not_inflate_each_other(self, client):
        """
        Two `Count`s over different reverse relations join both tables in one
        query. Without `distinct=True` a user with 3 trips and 2 posts reports
        6 of each — the classic Django multiple-join inflation.
        """
        from apps.trips.tests.factories import TripFactory

        author = UserFactory(email="riya@example.com")
        TripFactory.create_batch(3, user=author)
        PostFactory.create_batch(2, user=author)

        rows = {
            row["email"]: row
            for row in client.get(reverse("admin-user-list")).json()["data"]["results"]
        }

        assert rows["riya@example.com"]["trips_count"] == 3
        assert rows["riya@example.com"]["posts_count"] == 2
