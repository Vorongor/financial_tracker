from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from finances.models import Budget, Category, Transaction

User = get_user_model()


class FinancesModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser",
                                             password="1Qazcde3")
        self.user_ct = ContentType.objects.get_for_model(User)
        self.budget = Budget.objects.get(
            content_type=self.user_ct,
            object_id=self.user.id,
        )

        self.budget.save()
        self.income_cat = Category.objects.create(
            name="Salary",
            type=Category.Types.INCOME
        )
        self.expense_cat = Category.objects.create(
            name="Food",
            type=Category.Types.EXPENSE
        )

    def test_budget_recalc_logic(self):
        Transaction.objects.create(
            amount=Decimal("500.00"),
            type=Transaction.Types.INCOME,
            target=self.budget,
            payer=self.user,
            category=self.income_cat
        )

        Transaction.objects.create(
            amount=Decimal("200.00"),
            type=Transaction.Types.EXPENSE,
            target=self.budget,
            payer=self.user,
            category=self.expense_cat
        )

        Transaction.objects.create(
            amount=Decimal("400.00"),
            type=Transaction.Types.INCOME,
            target=self.budget,
            payer=self.user,
            category=self.income_cat
        )

        self.budget.recalc()

        self.assertEqual(self.budget.total_income, Decimal("900.00"))
        self.assertEqual(self.budget.total_expenses, Decimal("200.00"))
        self.assertEqual(self.budget.current_amount, Decimal("700.00"))

    def test_budget_negative_validation(self):
        self.budget.planned_amount = Decimal("-10.00")
        with self.assertRaises(ValidationError):
            self.budget.full_clean()

    def test_transaction_category_mismatch_income(self):
        transaction_ex = Transaction(
            amount=Decimal("100.00"),
            type=Transaction.Types.INCOME,
            target=self.budget,
            payer=self.user,
            category=self.expense_cat  # Помилка тут
        )
        with self.assertRaisesRegex(
                ValidationError,
                "Category type conflicts"
        ):
            transaction_ex.full_clean()

    def test_transaction_category_mismatch_expense(self):
        transaction_ex = Transaction(
            amount=Decimal("50.00"),
            type=Transaction.Types.EXPENSE,
            target=self.budget,
            payer=self.user,
            category=self.income_cat  # Помилка тут
        )
        with self.assertRaises(ValidationError):
            transaction_ex.save()

    def test_transaction_min_amount_validator(self):
        transaction_ex = Transaction(
            amount=Decimal("0.00"),
            type=Transaction.Types.INCOME,
            target=self.budget,
            payer=self.user
        )
        with self.assertRaises(ValidationError):
            transaction_ex.full_clean()

    def test_unique_budget_per_owner(self):
        with self.assertRaises(Exception):
            Budget.objects.create(
                content_type=self.user_ct,
                object_id=self.user.id
            )
