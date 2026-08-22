"""budget — `factory_boy` factories for this app's models."""

from decimal import Decimal

import factory

from apps.budget.constants import ExpenseCategory
from apps.budget.models import Expense
from apps.trips.tests.factories import TripFactory


class ExpenseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Expense

    trip = factory.SubFactory(TripFactory)
    category = ExpenseCategory.STAY
    title = factory.Sequence(lambda n: f"Expense {n}")
    amount = Decimal("1000.00")
    currency = "INR"
    is_estimated = True
