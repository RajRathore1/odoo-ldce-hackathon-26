"""community — `factory_boy` factories for this app's models."""

import factory

from apps.accounts.tests.factories import UserFactory
from apps.community.models import CommunityPost, PostComment, PostLike


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CommunityPost

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Post {n}")
    body = "Something worth sharing about the trip."
    is_published = True
    is_flagged = False


class PostCommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PostComment

    post = factory.SubFactory(PostFactory)
    user = factory.SubFactory(UserFactory)
    body = factory.Sequence(lambda n: f"Comment {n}")


class PostLikeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PostLike

    post = factory.SubFactory(PostFactory)
    user = factory.SubFactory(UserFactory)
