from decimal import Decimal

from django.db.models import (
    Sum,
    Case,
    When,
    Value,
    DecimalField,
    Count,
    Avg
)
from django.db.models.functions import TruncDay

from finances.models import Transaction
from dashboard.DTO import (
    DashboardKPI,
    CashflowPoint,
    CashflowTrend,
    PieDiagramData,
    TagPieDiagram,
    PieDiagramSegment,
    AnalyticsContext
)


class TransactionStatsService:
    @classmethod
    def _base_queryset(cls, ctx: AnalyticsContext):
        return Transaction.objects.filter(
            target_id=ctx.target_budget_id,
        )

    @classmethod
    def get_range_queryset(cls, ctx: AnalyticsContext):
        return cls._base_queryset(ctx).filter(
            date__range=(ctx.date_from, ctx.date_to), )

    @classmethod
    def get_kpi(cls, ctx: AnalyticsContext) -> DashboardKPI:
        qs = cls.get_range_queryset(ctx)

        aggregates = qs.aggregate(
            total_income=Sum(
                Case(
                    When(type=Transaction.Types.INCOME, then="amount"),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            ),
            total_expense=Sum(
                Case(
                    When(type=Transaction.Types.EXPENSE, then="amount"),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            ),
        )

        income = aggregates["total_income"] or Decimal("0")
        expense = aggregates["total_expense"] or Decimal("0")

        return DashboardKPI(
            total_income=income,
            total_expense=expense,
            balance=income - expense,
        )

    @classmethod
    def get_cashflow(cls, ctx: AnalyticsContext) -> CashflowTrend:
        qs = (
            cls.get_range_queryset(ctx)
            .annotate(day=TruncDay("date"))
            .values("day")
            .annotate(
                income=Sum(
                    Case(
                        When(type=Transaction.Types.INCOME, then="amount"),
                        default=Value(0),
                        output_field=DecimalField(),
                    )
                ),
                expense=Sum(
                    Case(
                        When(type=Transaction.Types.EXPENSE, then="amount"),
                        default=Value(0),
                        output_field=DecimalField(),
                    )
                ),
            )
            .order_by("day")
        )

        return CashflowTrend(
            points=[
                CashflowPoint(
                    date=row["day"],
                    income=row["income"] or Decimal("0"),
                    expense=row["expense"] or Decimal("0"),
                )
                for row in qs
            ]
        )

    @classmethod
    def get_pie_diagram(
            cls,
            target,
            transaction_type,
    ) -> PieDiagramData:
        qs = (
            Transaction.objects.filter(
                target=target.budget,
                type=transaction_type
            )
            .values("category__name")
            .annotate(total=Count("id"))
        )

        tags = {}
        for row in qs:
            name = row["category__name"] or "Other"
            tags[name] = row["total"]

        total_count = sum(tags.values())

        return PieDiagramData(
            count=total_count,
            tags=tags
        )

    @classmethod
    def get_category_stats(cls, ctx: AnalyticsContext, transaction_type):
        qs = (
            cls._base_queryset(ctx)
            .filter(type=transaction_type)
            .values("category__name", "category__type")
            .annotate(
                total_count=Count("id"),
                total_amount=Sum("amount"),
                avg_amount=Avg("amount"),
            )
            .order_by("-total_amount")
        )

        grand_total = sum(
            (row["total_amount"] or 0) for row in qs
        ) or Decimal("1")

        tags = []
        for row in qs:
            amount = row["total_amount"] or Decimal("0")
            tags.append(TagPieDiagram(
                tag_name=row["category__name"] or "Other",
                tag_type=row["category__type"] or transaction_type,
                total_count=row["total_count"],
                total_amount=int(amount),
                avg_amount=float(row["avg_amount"] or 0),
                percentage=round((amount / grand_total) * 100, 2),
            ))

        return PieDiagramSegment(points=tags)
