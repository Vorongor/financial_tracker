from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from groups.models import Group, GroupMembership
from finances.models import Budget
from datetime import date, timedelta

User = get_user_model()


class GroupModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass")

    def test_permanent_group_dates_validation(self):
        group = Group(
            name="Permanent Group",
            state=Group.States.PERMANENT,
            start_date=date.today()
        )
        with self.assertRaises(ValidationError):
            group.full_clean()

    def test_temporary_group_dates_logic(self):
        group = Group(
            name="Temp Group",
            state=Group.States.TEMPORARY,
            start_date=date.today(),
            end_date=date.today() - timedelta(days=1)
        )
        with self.assertRaises(ValidationError):
            group.full_clean()

    def test_group_budget_property(self):
        group = Group.objects.create(name="Finance Group", creator=self.user)
        budget = Budget.objects.get(
            content_type=ContentType.objects.get_for_model(Group),
            object_id=group.id,
        )
        budget.planned_amount = Decimal("1000.00")
        budget.save()

        self.assertEqual(group.budget.id, budget.id)
        self.assertEqual(group.budget.planned_amount, Decimal("1000.00"))

    def test_unique_membership_constraint(self):
        group = Group.objects.create(name="Unique Group")
        GroupMembership.objects.create(group=group, user=self.user)

        with self.assertRaises(Exception):
            GroupMembership.objects.create(group=group, user=self.user)
