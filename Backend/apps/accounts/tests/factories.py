"""accounts — `factory_boy` factories for this app's models."""

import factory

from apps.accounts.constants import UserRole
from apps.accounts.models import User

DEFAULT_PASSWORD = "Str0ng-Pass!2026"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = UserRole.USER
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """
        Hash the password rather than storing it raw. Without this every test
        user has an unusable password and `authenticate()` returns None, which
        looks like an auth bug rather than a fixture bug.
        """
        if not create:
            return
        obj.set_password(extracted or DEFAULT_PASSWORD)
        obj.save(update_fields=["password"])


class AdminFactory(UserFactory):
    role = UserRole.ADMIN
    is_staff = True
