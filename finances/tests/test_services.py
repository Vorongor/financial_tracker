from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from finances.models import Budget, Transaction, Category
from finances.services.history_service import TransactionHistoryService
from finances.services.transfers_service import TransfersService
from events.models import Event

User = get_user_model()


class TransfersServiceTest(TestCase):
    def setUp(self):
        self.user_from = User.objects.create_user(
            username="sender",
            password="pass"
        )
        self.budget_from = Budget.objects.get(
            content_type=ContentType.objects.get_for_model(User),
            object_id=self.user_from.id,
        )

        self.budget_from.start_amount = Decimal("1000.00")
        self.budget_from.save()

        self.user_to = User.objects.create_user(
            username="receiver",
            password="pass"
        )
        self.budget_to = Budget.objects.get(
            content_type=ContentType.objects.get_for_model(User),
            object_id=self.user_to.id,
        )

        Category.objects.create(
            name="Spent on donate",
            type=Category.Types.EXPENSE
        )
        Category.objects.create(
            name="Receive from saved",
            type=Category.Types.INCOME
        )
        self.general_cat = Category.objects.create(
            name="General",
            type=Category.Types.EXPENSE
        )

    def test_transfer_between_budgets_logic(self):
        amount = Decimal("300.00")

        TransfersService.transfer_between_budgets(
            amount=amount,
            from_budget=self.budget_from,
            to_budget=self.budget_to,
            payer=self.user_from,
            date=timezone.now()
        )

        self.budget_from.refresh_from_db()
        self.budget_to.refresh_from_db()

        self.assertEqual(self.budget_from.current_amount, Decimal("700.00"))
        self.assertEqual(self.budget_from.total_expenses, Decimal("300.00"))

        self.assertEqual(self.budget_to.current_amount, Decimal("300.00"))
        self.assertEqual(self.budget_to.total_income, Decimal("300.00"))

        self.assertEqual(Transaction.objects.count(), 2)

    def test_top_up_budget(self):
        amount = Decimal("500.00")
        TransfersService.top_up_budget(
            user=self.user_to,
            amount=amount,
            note="Salary"
        )
        self.budget_to.refresh_from_db()
        self.assertEqual(self.budget_to.current_amount, Decimal("500.00"))

    def test_set_expense(self):
        amount = Decimal("150.00")
        TransfersService.set_expense(
            user=self.user_from,
            amount=amount,
            category=self.general_cat
        )
        self.budget_from.refresh_from_db()
        self.assertEqual(self.budget_from.current_amount, Decimal("850.00"))

    def test_get_budget_by_content_type_invalid_owner(self):
        with self.assertRaises(ValueError):
            TransfersService.get_budget_by_content_type("invalid_type", 1)


    def test_get_user_transactions(self):
        Transaction.objects.create(
            amount=Decimal("10.00"),
            type=Transaction.Types.EXPENSE,
            target=self.budget_from,
            payer=self.user_from
        )

        transactions = TransactionHistoryService.get_user_transactions(
            self.user_from.id)
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions.first().payer, self.user_from)

    def test_get_event_transactions(self):
        event = Event.objects.create(name="Trip", planned_amount=5000)
        event_budget = Budget.objects.get(
            content_type=ContentType.objects.get_for_model(Event),
            object_id=event.id
        )

        Transaction.objects.create(
            amount=Decimal("1000.00"),
            type=Transaction.Types.INCOME,
            target=event_budget,
            payer=self.user_from
        )

        history = TransactionHistoryService.get_event_transactions(event.id)
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().target, event_budget)
