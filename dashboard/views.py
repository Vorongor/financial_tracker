from _datetime import datetime

from django.utils import timezone
from django.views.generic import TemplateView

from dashboard.DTO import AnalyticsContext
from dashboard.services.transactions_stats import TransactionStatsService
from finances.models import Transaction


class HomeDashboard(TemplateView):
    template_name = "dashboard/dashboard.html"


class PersonalDashView(TemplateView):
    template_name = "dashboard/personal-dash.html"

    def get_context_data(self, **kwargs):
        context = super(PersonalDashView, self).get_context_data(**kwargs)

        user = self.request.user

        today = timezone.now().date()
        date_from = today.replace(day=1)
        context["default_from"] = date_from.strftime("%Y-%m-%d")
        context["default_to"] = today.strftime("%Y-%m-%d")

        context_obj = AnalyticsContext(
            target_budget_id=user.budget.id,
            date_from=date_from,
            date_to=today,
        )

        kpi = TransactionStatsService.get_kpi(ctx=context_obj)
        cashflow = TransactionStatsService.get_cashflow(ctx=context_obj)

        pie_income = TransactionStatsService.get_pie_diagram(
            target=user,
            transaction_type=Transaction.Types.INCOME,
        )

        pie_expense = TransactionStatsService.get_pie_diagram(
            target=user,
            transaction_type=Transaction.Types.EXPENSE,
        )

        pie_tag_incomes = TransactionStatsService.get_category_stats(
            ctx=context_obj,
            transaction_type=Transaction.Types.INCOME,
        )

        pie_tag_expense = TransactionStatsService.get_category_stats(
            ctx=context_obj,
            transaction_type=Transaction.Types.EXPENSE,
        )

        context.update({
            "kpi": kpi,
            "cashflow": cashflow,
            "pie_income": pie_income,
            "pie_expense": pie_expense,
            "pie_tag_incomes": pie_tag_incomes,
            "pie_tag_expense": pie_tag_expense,
        })

        return context


class PersonalDashStatsView(TemplateView):
    template_name = "dashboard/components/stats_block.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        date_from = self.request.GET["from"]
        date_to = self.request.GET["to"]

        context_obj = AnalyticsContext(
            target_budget_id=user.budget.id,
            date_from=datetime.strptime(date_from, "%Y-%m-%d"),
            date_to=datetime.strptime(date_to, "%Y-%m-%d"),
        )

        context["kpi"] = TransactionStatsService.get_kpi(
            ctx=context_obj
        )
        context["cashflow"] = TransactionStatsService.get_cashflow(
            ctx=context_obj
        )

        return context
