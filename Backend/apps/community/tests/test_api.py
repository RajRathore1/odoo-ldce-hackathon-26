"""community — Status codes, envelope shape, permissions."""

from datetime import date

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import DEFAULT_PASSWORD, UserFactory
from apps.activities.constants import ActivityType
from apps.activities.tests.factories import ActivityFactory
from apps.community.models import CommunityPost, PostComment, PostLike
from apps.community.tests.factories import PostCommentFactory, PostFactory, PostLikeFactory
from apps.geo.tests.factories import CityFactory, CountryFactory
from apps.trips.tests.factories import TripFactory

pytestmark = pytest.mark.django_db

TODAY = date.today()
POSTS_URL = reverse("post-list")


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
def author():
    return UserFactory(
        email="riya@example.com",
        first_name="Riya",
        last_name="Sharma",
        phone_number="+91 98250 11111",
    )


@pytest.fixture
def client(author):
    return signed_in(author)


@pytest.fixture
def reader():
    return UserFactory(email="reader@example.com", first_name="Sam")


def detail_url(post_id) -> str:
    return reverse("post-detail", args=[post_id])


def like_url(post_id) -> str:
    return reverse("post-like", args=[post_id])


def comments_url(post_id) -> str:
    return reverse("post-comment-list", args=[post_id])


# ----------------------------------------------------------------------- feed


class TestFeed:
    def test_it_requires_authentication(self):
        assert APIClient().get(POSTS_URL).status_code == 401

    def test_it_uses_cursor_pagination(self, client, author):
        """
        A feed grows at the top, so page numbers would shift a row from page 2
        onto page 3 between requests and show it twice. The trade-off is no
        `count`, which a feed does not need.
        """
        PostFactory(user=author)

        body = client.get(POSTS_URL).json()["data"]

        assert "count" not in body["pagination"]
        assert set(body["pagination"]) == {
            "page_size",
            "has_next",
            "has_previous",
            "next",
            "previous",
        }

    def test_the_row_shape(self, client, author):
        india = CountryFactory(name="India", iso2="IN")
        city = CityFactory(country=india, name="Bir")
        trip = TripFactory(user=author, name="Himachal Winter")
        activity = ActivityFactory(city=city, activity_type=ActivityType.ADVENTURE)
        post = PostFactory(
            user=author,
            title="Bir Billing was unreal",
            body="Flew at sunrise.",
            city=city,
            trip=trip,
            activity=activity,
        )

        row = client.get(POSTS_URL).json()["data"]["results"][0]

        assert row["id"] == post.pk
        assert row["title"] == "Bir Billing was unreal"
        assert row["author"] == {"first_name": "Riya", "avatar": None}
        assert row["city"]["name"] == "Bir"
        assert row["city"]["country_name"] == "India"
        assert row["trip"]["name"] == "Himachal Winter"
        assert row["activity_name"] == activity.name
        assert row["likes_count"] == 0
        assert row["comments_count"] == 0
        assert row["is_liked_by_me"] is False

    def test_the_feed_leaks_no_author_pii(self, client, author):
        """A feed is a public surface — the author is the same reduced shape the
        shared trip page uses."""
        PostFactory(user=author)

        raw = client.get(POSTS_URL).content.decode()

        for private in ("riya@example.com", "Sharma", "+91 98250 11111"):
            assert private not in raw, private

    def test_it_shows_other_peoples_posts(self, client):
        """Not owner-scoped — a feed you can only read your own posts in is not a feed."""
        theirs = PostFactory(user=UserFactory())

        rows = client.get(POSTS_URL).json()["data"]["results"]

        assert [row["id"] for row in rows] == [theirs.pk]

    def test_unpublished_and_flagged_posts_are_hidden(self, client, author):
        PostFactory(user=author, is_published=False)
        PostFactory(user=author, is_flagged=True)
        visible = PostFactory(user=author)

        rows = client.get(POSTS_URL).json()["data"]["results"]

        assert [row["id"] for row in rows] == [visible.pk]

    def test_a_deleted_post_is_hidden(self, client, author):
        PostFactory(user=author).delete()

        assert client.get(POSTS_URL).json()["data"]["results"] == []

    def test_is_liked_by_me_is_per_caller(self, client, author, reader):
        post = PostFactory(user=author)
        PostLikeFactory(post=post, user=reader)

        mine = client.get(POSTS_URL).json()["data"]["results"][0]
        theirs = signed_in(reader).get(POSTS_URL).json()["data"]["results"][0]

        assert mine["is_liked_by_me"] is False
        assert theirs["is_liked_by_me"] is True

    def test_it_filters_by_city_and_activity_type(self, client, author):
        city = CityFactory()
        match = PostFactory(
            user=author,
            city=city,
            activity=ActivityFactory(city=city, activity_type=ActivityType.FOOD),
        )
        PostFactory(user=author, city=CityFactory())

        by_city = client.get(POSTS_URL, {"city": city.pk}).json()["data"]["results"]
        by_type = client.get(POSTS_URL, {"activity_type": "FOOD"}).json()["data"]["results"]

        assert [row["id"] for row in by_city] == [match.pk]
        assert [row["id"] for row in by_type] == [match.pk]

    def test_it_searches_title_and_body(self, client, author):
        match = PostFactory(user=author, title="Paragliding", body="tandem flight")
        PostFactory(user=author, title="Museum day", body="guided")

        rows = client.get(POSTS_URL, {"search": "tandem"}).json()["data"]["results"]

        assert [row["id"] for row in rows] == [match.pk]

    def test_it_can_be_ordered_by_popularity(self, client, author):
        quiet = PostFactory(user=author, likes_count=1)
        loved = PostFactory(user=author, likes_count=99)

        rows = client.get(POSTS_URL, {"ordering": "-likes_count"}).json()["data"]["results"]

        assert [row["id"] for row in rows] == [loved.pk, quiet.pk]

    def test_query_count_does_not_grow_with_the_page(
        self, client, author, django_assert_num_queries
    ):
        """Trap #9 — every row nests an author, a city, a country and a trip."""
        PostFactory.create_batch(3, user=author, city=CityFactory())
        with django_assert_num_queries(2) as captured:
            client.get(POSTS_URL)

        PostFactory.create_batch(12, user=author, city=CityFactory())
        with django_assert_num_queries(len(captured.captured_queries)):
            client.get(POSTS_URL)


class TestCreatePost:
    def payload(self, **overrides) -> dict:
        return {"title": "Bir Billing", "body": "Worth the drive.", **overrides}

    def test_it_publishes_a_post(self, client, author):
        response = client.post(POSTS_URL, self.payload(), format="json")
        body = response.json()

        assert response.status_code == 201
        assert body["message"] == "Post published."
        assert body["data"]["author"]["first_name"] == "Riya"
        assert CommunityPost.objects.get().user == author

    def test_a_title_and_body_are_required(self, client):
        response = client.post(POSTS_URL, {"title": ""}, format="json")

        assert response.status_code == 400
        assert "body" in response.json()["errors"]["fields"]

    def test_it_can_only_attach_your_own_trip(self, client):
        """
        Otherwise anybody could publish a post carrying a stranger's trip — and
        `share_url` in the payload would hand out a working share token for it.
        """
        stranger = TripFactory(user=UserFactory())

        response = client.post(POSTS_URL, self.payload(trip=stranger.pk), format="json")

        assert response.status_code == 400
        assert "trip" in response.json()["errors"]["fields"]

    def test_the_moderation_flags_cannot_be_set_by_the_author(self, client):
        client.post(
            POSTS_URL, self.payload(is_flagged=False, is_published=False), format="json"
        )

        post = CommunityPost.objects.get()
        assert post.is_published is True
        assert post.is_flagged is False

    def test_the_counters_cannot_be_seeded(self, client):
        client.post(POSTS_URL, self.payload(likes_count=500), format="json")

        assert CommunityPost.objects.get().likes_count == 0


class TestPostDetail:
    def test_anybody_signed_in_can_read_a_post(self, reader, author):
        post = PostFactory(user=author)

        assert signed_in(reader).get(detail_url(post.pk)).status_code == 200

    def test_only_the_author_can_edit(self, reader, author):
        post = PostFactory(user=author, title="Mine")

        response = signed_in(reader).patch(
            detail_url(post.pk), {"title": "Hijacked"}, format="json"
        )

        assert response.status_code == 403
        post.refresh_from_db()
        assert post.title == "Mine"

    def test_the_author_can_edit(self, client, author):
        post = PostFactory(user=author)

        response = client.patch(detail_url(post.pk), {"title": "Rewritten"}, format="json")

        assert response.status_code == 200
        assert response.json()["message"] == "Post updated."
        post.refresh_from_db()
        assert post.title == "Rewritten"

    def test_only_the_author_can_delete(self, reader, author):
        post = PostFactory(user=author)

        assert signed_in(reader).delete(detail_url(post.pk)).status_code == 403
        assert CommunityPost.objects.filter(pk=post.pk).exists()

    def test_the_authors_delete_is_soft(self, client, author):
        post = PostFactory(user=author)

        response = client.delete(detail_url(post.pk))

        assert response.status_code == 204
        assert not CommunityPost.objects.filter(pk=post.pk).exists()
        assert CommunityPost.all_objects.filter(pk=post.pk).exists()


# ---------------------------------------------------------------------- likes


class TestLikes:
    def test_liking_moves_the_counter(self, reader, author):
        post = PostFactory(user=author)

        response = signed_in(reader).post(like_url(post.pk))
        body = response.json()

        assert response.status_code == 200
        assert body["message"] == "Post liked."
        assert body["data"]["likes_count"] == 1
        assert body["data"]["is_liked_by_me"] is True
        post.refresh_from_db()
        assert post.likes_count == 1

    def test_liking_twice_is_a_conflict(self, reader, author):
        post = PostFactory(user=author)
        api = signed_in(reader)
        api.post(like_url(post.pk))

        response = api.post(like_url(post.pk))

        assert response.status_code == 409
        post.refresh_from_db()
        assert post.likes_count == 1
        assert PostLike.objects.filter(post=post).count() == 1

    def test_unliking_removes_the_row_for_real(self, reader, author):
        """A soft-deleted like would keep occupying the unique key (trap #3)."""
        post = PostFactory(user=author)
        api = signed_in(reader)
        api.post(like_url(post.pk))

        response = api.delete(like_url(post.pk))

        assert response.status_code == 200
        assert response.json()["data"]["likes_count"] == 0
        assert not PostLike.objects.filter(post=post).exists()

    def test_a_post_can_be_liked_again_after_unliking(self, reader, author):
        post = PostFactory(user=author)
        api = signed_in(reader)
        api.post(like_url(post.pk))
        api.delete(like_url(post.pk))

        assert api.post(like_url(post.pk)).status_code == 200
        post.refresh_from_db()
        assert post.likes_count == 1

    def test_unliking_something_you_never_liked_is_a_quiet_200(self, reader, author):
        """The desired end state already holds, so this is not an error."""
        post = PostFactory(user=author)

        response = signed_in(reader).delete(like_url(post.pk))

        assert response.status_code == 200
        post.refresh_from_db()
        assert post.likes_count == 0

    def test_the_counter_cannot_go_negative(self, reader, author):
        post = PostFactory(user=author)
        api = signed_in(reader)

        for _ in range(3):
            api.delete(like_url(post.pk))

        post.refresh_from_db()
        assert post.likes_count == 0

    def test_two_users_both_count(self, author, reader):
        post = PostFactory(user=author)
        signed_in(reader).post(like_url(post.pk))
        signed_in(UserFactory()).post(like_url(post.pk))

        post.refresh_from_db()
        assert post.likes_count == 2

    def test_an_unpublished_post_cannot_be_liked(self, reader, author):
        post = PostFactory(user=author, is_published=False)

        assert signed_in(reader).post(like_url(post.pk)).status_code == 404


# ------------------------------------------------------------------- comments


class TestComments:
    def test_commenting_moves_the_counter(self, reader, author):
        post = PostFactory(user=author)

        response = signed_in(reader).post(
            comments_url(post.pk), {"body": "Great write-up."}, format="json"
        )

        assert response.status_code == 201
        assert response.json()["message"] == "Comment added."
        post.refresh_from_db()
        assert post.comments_count == 1

    def test_replies_nest_one_level(self, client, reader, author):
        post = PostFactory(user=author)
        top = PostCommentFactory(post=post, user=author, body="Top")
        PostCommentFactory(post=post, user=reader, parent=top, body="Reply")

        rows = client.get(comments_url(post.pk)).json()["data"]["results"]

        assert len(rows) == 1
        assert rows[0]["body"] == "Top"
        assert [reply["body"] for reply in rows[0]["replies"]] == ["Reply"]

    def test_a_reply_to_a_reply_is_rejected(self, client, author):
        post = PostFactory(user=author)
        top = PostCommentFactory(post=post, user=author)
        reply = PostCommentFactory(post=post, user=author, parent=top)

        response = client.post(
            comments_url(post.pk), {"body": "Too deep", "parent": reply.pk}, format="json"
        )

        assert response.status_code == 400
        assert "parent" in response.json()["errors"]["fields"]

    def test_a_parent_from_another_post_is_rejected(self, client, author):
        post = PostFactory(user=author)
        elsewhere = PostCommentFactory()

        response = client.post(
            comments_url(post.pk),
            {"body": "Wrong thread", "parent": elsewhere.pk},
            format="json",
        )

        assert response.status_code == 400
        assert "parent" in response.json()["errors"]["fields"]

    def test_only_the_author_can_delete_a_comment(self, reader, author):
        post = PostFactory(user=author)
        comment = PostCommentFactory(post=post, user=author)

        url = reverse("post-comment-detail", args=[comment.pk])
        assert signed_in(reader).delete(url).status_code == 403
        assert PostComment.objects.filter(pk=comment.pk).exists()

    def test_deleting_a_comment_takes_its_replies_and_the_counter(self, client, author):
        """
        A reply whose parent is gone is unreachable but still counted, so the
        subtree goes together and the counter drops by all of it.
        """
        post = PostFactory(user=author)
        top = PostCommentFactory(post=post, user=author)
        PostCommentFactory.create_batch(2, post=post, user=author, parent=top)
        CommunityPost.objects.filter(pk=post.pk).update(comments_count=3)

        response = client.delete(reverse("post-comment-detail", args=[top.pk]))

        assert response.status_code == 204
        assert PostComment.objects.filter(post=post).count() == 0
        post.refresh_from_db()
        assert post.comments_count == 0

    def test_comments_on_an_unpublished_post_are_a_404(self, client, author):
        post = PostFactory(user=author, is_published=False)

        assert client.get(comments_url(post.pk)).status_code == 404

    def test_query_count_does_not_grow_with_the_thread(
        self, client, author, django_assert_num_queries
    ):
        post = PostFactory(user=author)
        for _ in range(2):
            top = PostCommentFactory(post=post, user=author)
            PostCommentFactory(post=post, user=author, parent=top)

        with django_assert_num_queries(5) as captured:
            client.get(comments_url(post.pk))

        for _ in range(6):
            top = PostCommentFactory(post=post, user=author)
            PostCommentFactory(post=post, user=author, parent=top)

        with django_assert_num_queries(len(captured.captured_queries)):
            client.get(comments_url(post.pk))


class TestRecalculateCounters:
    def test_it_repairs_drifted_counters(self, author):
        from apps.community.services import recalculate_post_counters

        post = PostFactory(user=author)
        PostLikeFactory.create_batch(2, post=post)
        PostCommentFactory.create_batch(3, post=post)
        CommunityPost.objects.filter(pk=post.pk).update(likes_count=999, comments_count=999)

        recalculate_post_counters()

        post.refresh_from_db()
        assert post.likes_count == 2
        assert post.comments_count == 3

    def test_a_deleted_comment_does_not_count(self, author):
        from apps.community.services import recalculate_post_counters

        post = PostFactory(user=author)
        PostCommentFactory(post=post)
        PostCommentFactory(post=post).delete()

        recalculate_post_counters()

        post.refresh_from_db()
        assert post.comments_count == 1
