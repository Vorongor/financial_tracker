from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from dashboard.DTO import AnalyticsContext
from dashboard.services.transactions_stats import TransactionStatsService
from finances.models import Transaction, Category


class TransactionStatsServiceTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="1Qazcde3",
        )
        self.budget = self.user.budget

        self.now = timezone.now()

    def create_category(self, name, type_):
        return Category.objects.create(name=name, category_type=type_)

    def create_transaction(
            self,
            *,
            amount,
            type_,
            category,
            date=None,
    ):
        return Transaction.objects.create(
            target=self.budget,
            category=category,
            transaction_type=type_,
            amount=Decimal(amount),
            date=date or self.now,
            payer=self.user,
        )

    def ctx(self, *, date_from=None, date_to=None):
        return AnalyticsContext(
            target_budget_id=self.budget.id,
            date_from=date_from or self.now - timedelta(days=1),
            date_to=date_to or self.now + timedelta(days=1),
        )

    def test_get_kpi(self):
        income = self.create_category(
            "Salary",
            Transaction.Types.INCOME
        )
        expense = self.create_category(
            "Food",
            Transaction.Types.EXPENSE
        )

        self.create_transaction(
            amount="1000",
            type_=Transaction.Types.INCOME,
            category=income
        )
        self.create_transaction(
            amount="300",
            type_=Transaction.Types.EXPENSE,
            category=expense
        )

        kpi = TransactionStatsService.get_kpi(self.ctx())

        self.assertEqual(kpi.total_income, Decimal("1000"))
        self.assertEqual(kpi.total_expense, Decimal("300"))
        self.assertEqual(kpi.balance, Decimal("700"))

    def test_get_cashflow(self):
        food = self.create_category("Food", Transaction.Types.EXPENSE)

        day1 = self.now - timedelta(days=1)
        day2 = self.now

        self.create_transaction(
            amount="50",
            type_=Transaction.Types.EXPENSE,
            category=food,
            date=day1
        )
        self.create_transaction(
            amount="70",
            type_=Transaction.Types.EXPENSE,
            category=food,
            date=day2
        )

        trend = TransactionStatsService.get_cashflow(
            self.ctx(
                date_from=day1 - timedelta(hours=1),
                date_to=day2 + timedelta(hours=1),
            )
        )

        self.assertEqual(len(trend.points), 2)
        self.assertEqual(trend.points[0].expense, Decimal("50"))
        self.assertEqual(trend.points[1].expense, Decimal("70"))

    def test_get_pie_diagram(self):
        food = self.create_category("Food", Transaction.Types.EXPENSE)
        transport = self.create_category("Transport",
                                         Transaction.Types.EXPENSE)

        self.create_transaction(
            amount="10",
            type_=Transaction.Types.EXPENSE,
            category=food
        )
        self.create_transaction(
            amount="20",
            type_=Transaction.Types.EXPENSE,
            category=food
        )
        self.create_transaction(
            amount="15",
            type_=Transaction.Types.EXPENSE,
            category=transport
        )

        data = TransactionStatsService.get_pie_diagram(
            target=self.user,
            transaction_type=Transaction.Types.EXPENSE,
        )

        self.assertEqual(data.count, 3)
        self.assertEqual(data.tags["Food"], 2)
        self.assertEqual(data.tags["Transport"], 1)

    def test_get_category_stats(self):
        food = self.create_category("Food", Transaction.Types.EXPENSE)

        self.create_transaction(
            amount="10",
            type_=Transaction.Types.EXPENSE,
            category=food
        )
        self.create_transaction(
            amount="30",
            type_=Transaction.Types.EXPENSE,
            category=food
        )

        result = TransactionStatsService.get_category_stats(
            self.ctx(),
            Transaction.Types.EXPENSE,
        )

        point = result.points[0]

        self.assertEqual(point.total_count, 2)
        self.assertEqual(point.total_amount, 40)
        self.assertEqual(point.avg_amount, 20.0)
        self.assertEqual(point.percentage, 100.0)
