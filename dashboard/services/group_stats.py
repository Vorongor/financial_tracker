from collections import defaultdict
from decimal import Decimal

from dashboard.DTO import BarChartData
from finances.models import Transaction
from groups.models import Group


class GroupStatsService:
    @classmethod
    def get_bar_chart_data(cls, pk: int) -> BarChartData:
        group = Group.objects.get(pk=pk)

        transactions = (
            Transaction.objects
            .filter(target=group.budget)
            .order_by("date")
        )

        income_map = defaultdict(Decimal)
        expense_map = defaultdict(Decimal)

        for tx in transactions:
            label = tx.date.strftime("%Y-%m-%d")

            if tx.transaction_type == Transaction.Types.INCOME:
                income_map[label] += tx.amount
            elif tx.transaction_type == Transaction.Types.EXPENSE:
                expense_map[label] += tx.amount

        labels = sorted(set(income_map.keys()) | set(expense_map.keys()))

        return BarChartData(
            labels=labels,
            incomes=[float(income_map[label]) for label in labels],
            expenses=[-float(expense_map[label]) for label in labels],
        )
