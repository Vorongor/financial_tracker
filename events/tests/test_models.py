from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase

from events.models import Event, EventMembership
from finances.models import Budget


User = get_user_model()


class EventModelCleanTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="creator", password="test123"
        )

    def test_clean_raises_error_if_end_date_before_start_date(self):
        event = Event(
            name="Invalid dates",
            start_date=date.today(),
            end_date=date.today() - timedelta(days=1),
            creator=self.user,
        )

        with self.assertRaises(ValidationError) as ctx:
            event.clean()

        self.assertIn("end_date", ctx.exception.message_dict)

    def test_clean_raises_error_if_planned_amount_negative(self):
        event = Event(
            name="Negative amount",
            planned_amount=Decimal("-10.00"),
            creator=self.user,
        )

        with self.assertRaises(ValidationError) as ctx:
            event.clean()

        self.assertIn("planned_amount", ctx.exception.message_dict)

    def test_clean_passes_for_valid_data(self):
        event = Event(
            name="Valid event",
            start_date=date.today(),
            end_date=date.today(),
            planned_amount=Decimal("100.00"),
            creator=self.user,
        )
        event.clean()


class EventBudgetPropertyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="creator", password="test123"
        )
        self.event = Event.objects.create(
            name="Event with budget",
            creator=self.user,
        )

    def test_budget_property_returns_created_budget(self):
        self.assertIsNotNone(self.event.budget)

    def test_budget_property_returns_related_budget(self):
        ct = ContentType.objects.get_for_model(self.event)

        budget = Budget.objects.get(
            content_type=ct,
            object_id=self.event.id,
        )

        self.assertEqual(self.event.budget, budget)


class EventMembershipConstraintTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="member", password="test123"
        )
        self.event = Event.objects.create(name="Event")

    def test_unique_event_user_constraint(self):
        EventMembership.objects.create(event=self.event, user=self.user)

        with self.assertRaises(Exception):
            EventMembership.objects.create(event=self.event, user=self.user)
