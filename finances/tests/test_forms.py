from decimal import Decimal
from django.test import TestCase
from finances.models import Category, Transaction
from finances.forms import (
    TopUpBudgetForm,
    SetExpenseBudgetForm,
    TransferCreateForm
)


class FinancesFormTest(TestCase):
    def setUp(self):
        self.income_cat = Category.objects.create(
            name="Salary",
            category_type=Category.Types.INCOME
        )
        self.expense_cat = Category.objects.create(
            name="Food",
            category_type=Category.Types.EXPENSE
        )

    def test_top_up_form_valid(self):
        form_data = {
            "amount": Decimal("100.00"),
            "category": self.income_cat.id,
            "note": "Bonus"
        }
        form = TopUpBudgetForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_top_up_form_invalid_amount(self):
        form = TopUpBudgetForm(data={"amount": 0})
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_top_up_form_category_queryset(self):
        form = TopUpBudgetForm()
        queryset = form.fields["category"].queryset
        self.assertIn(self.income_cat, queryset)
        self.assertNotIn(self.expense_cat, queryset)

    def test_set_expense_form_category_queryset(self):
        form = SetExpenseBudgetForm()
        queryset = form.fields["category"].queryset
        self.assertIn(self.expense_cat, queryset)
        self.assertNotIn(self.income_cat, queryset)

    def test_transfer_form_mismatch_logic_prevention(self):
        form_data = {
            "amount": Decimal("50.00"),
            "transaction_type": Transaction.Types.INCOME,
            "category": self.expense_cat.id,
        }
        form = TransferCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("category", form.errors)

    def test_budget_edit_form_negative_planned_amount(self):
        from finances.forms import BudgetEditForm
        form = BudgetEditForm(data={
            "planned_amount": -500,
            "start_amount": 100
        })
        self.assertFalse(form.is_valid())
        self.assertIn("planned_amount", form.errors)
