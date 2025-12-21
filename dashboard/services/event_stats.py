from datetime import timedelta
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from finances.models import Transaction


class EventAnalyticsService:
    @staticmethod
    def get_event_stats(event, budget):
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
    def get_social_stats(event, budget):
        leaderboard = []
        if budget:
            leaderboard = (
                budget.transactions.filter(type="Income")
                .values('payer__username', 'payer__first_name',
                        'payer__last_name')
                .annotate(total_contributed=Sum('amount'))
                .order_by('-total_contributed')[:5]
            )

        status_counts = (
            event.memberships.values('role')
            .annotate(count=Count('id'))
        )

        status_labels = [s['role'] for s in status_counts]
        status_data = [s['count'] for s in status_counts]

        return {
            "leaderboard": leaderboard,
            "status_labels": status_labels,
            "status_data": status_data,
        }
