from datetime import timedelta, date
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Case, When
from django.db.models.fields import DecimalField
from django.db.models.functions import TruncDate, TruncDay
from django.utils import timezone

from finances.models import Transaction, Budget

User = get_user_model()

class EventAnalyticsService:
    @staticmethod
    def get_event_accumulative_stats(
            event: User,
            budget: Budget
    ) -> dict[str, Any]:
        planned = float(budget.planned_amount) or 1.0
        current = float(budget.current_amount)
        percent = round((current / planned) * 100, 1)

        end_date = event.end_date or timezone.now().date()
        start_date = end_date - timedelta(days=30)

        transactions = (
            Transaction.objects
            .filter(target=budget)
            .annotate(day=TruncDate("date"))
            .values("day")
            .annotate(total_amount=Sum("amount"))
            .order_by("day")
        )

        daily_map = {
            t["day"]: float(t["total_amount"])
            for t in transactions
        }

        labels = []
        data_points = []

        for i in range(31):
            day = start_date + timedelta(days=i)
            labels.append(day.strftime("%d %b"))
            data_points.append(daily_map.get(day, 0.0))

        return {
            "percent": min(percent, 100),
            "gauge_color": "#28a745" if percent >= 100 else "#ffc107",
            "labels": labels,
            "data_points": data_points,
        }

    @staticmethod
    def get_social_stats(event: User, budget: Budget) -> dict[str, Any]:
        leaderboard = []
        if budget:
            leaderboard = (
                budget.transactions.filter(transaction_type="Income")
                .values("payer__username", "payer__first_name",
                        "payer__last_name")
                .annotate(total_contributed=Sum("amount"))
                .order_by("-total_contributed")[:5]
            )

        status_counts = (
            event.memberships.values("role")
            .annotate(count=Count("id"))
        )

        status_labels = [s["role"] for s in status_counts]
        status_data = [s["count"] for s in status_counts]

        return {
            "leaderboard": leaderboard,
            "status_labels": status_labels,
            "status_data": status_data,
        }

    @classmethod
    def get_event_savings_stats(cls, budget: Budget) -> dict[str, Any]:
        stats = (
            Transaction.objects
            .filter(target=budget)
            .annotate(day=TruncDay('date'))
            .values('day')
            .annotate(
                income=Sum(
                    Case(
                        When(transaction_type=Transaction.Types.INCOME,
                             then='amount'),
                        default=0,
                        output_field=DecimalField()
                    )
                ),
                expense=Sum(
                    Case(
                        When(transaction_type=Transaction.Types.EXPENSE,
                             then='amount'),
                        default=0,
                        output_field=DecimalField()
                    )
                )
            )
            .order_by('day')
        )

        labels = []
        data_points = []

        for entry in stats:
            labels.append(entry['day'].strftime('%d.%m.%Y'))
            income = entry['income'] or 0
            expense = entry['expense'] or 0
            net_amount = float(income - expense)
            data_points.append(net_amount)

        return {
            "labels": labels,
            "data_points": data_points
        }

    @classmethod
    def get_event_expense_stats(
            cls,
            start: date,
            end: date,
            budget: Budget,
            total_expense: Decimal) -> dict[str, Any]:

        stats_query = (
            Transaction.objects
            .filter(target=budget, date__range=(start, end))
            .annotate(day=TruncDay('date'))
            .values('day')
            .annotate(
                expense=Sum(
                    Case(
                        When(transaction_type=Transaction.Types.EXPENSE,
                             then='amount'),
                        default=0,
                        output_field=DecimalField()
                    )
                )
            )
        )
        actual_expenses = {
            entry['day'].date(): float(entry['expense'])
            for entry in stats_query
        }

        delta = end - start
        total_days = delta.days + 1

        daily_plan_reduction = float(
            total_expense) / total_days if total_days > 0 else 0

        labels = []
        real_points = []
        project_points = []

        current_real_balance = float(total_expense)
        current_project_balance = float(total_expense)

        for i in range(total_days):
            current_date = start + timedelta(days=i)
            labels.append(current_date.strftime('%d.%m.%Y'))

            current_project_balance -= daily_plan_reduction
            project_points.append(max(0, current_project_balance))

            day_expense = actual_expenses.get(current_date, 0)
            current_real_balance -= day_expense
            real_points.append(current_real_balance)

        return {
            "labels": labels,
            "real_points": real_points,
            "project_points": project_points,
        }

    @classmethod
    def accumulate_stats(
            cls,
            start: date,
            end: date,
            budget: Budget,
            planed_goal: Decimal
    ) -> dict[str, Any]:

        stats_query = (
            Transaction.objects
            .filter(target=budget, date__range=(start, end))
            .annotate(day=TruncDay('date'))
            .values('day')
            .annotate(
                expense=Sum(
                    Case(
                        When(transaction_type=Transaction.Types.INCOME,
                             then='amount'),
                        default=0,
                        output_field=DecimalField()
                    )
                )
            )
        )
        actual_incomes = {
            entry['day'].date(): float(entry['expense'])
            for entry in stats_query
        }

        delta = end - start
        total_days = delta.days + 1

        daily_plan_receives = float(
            planed_goal) / total_days if total_days > 0 else 0

        labels = []
        real_points = []
        project_points = []

        current_real_balance = float(0)
        current_project_balance = float(0)

        for i in range(total_days):
            current_date = start + timedelta(days=i)
            labels.append(current_date.strftime('%d.%m.%Y'))

            current_project_balance += daily_plan_receives
            project_points.append(current_project_balance)

            day_incomes = actual_incomes.get(current_date, 0)
            current_real_balance += day_incomes
            real_points.append(current_real_balance)

        return {
            "labels": labels,
            "real_points": real_points,
            "project_points": project_points,
        }