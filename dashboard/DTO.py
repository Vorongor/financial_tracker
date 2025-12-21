from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List


@dataclass(frozen=True)
class AnalyticsContext:
    target_budget_id: int
    date_from: date
    date_to: date


@dataclass
class DashboardKPI:
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal


@dataclass
class CashflowPoint:
    date: date
    income: Decimal
    expense: Decimal


@dataclass
class CashflowTrend:
    points: List[CashflowPoint]


@dataclass
class PieDiagramData:
    count: int
    tags: dict[str, int]


@dataclass
class TagPieDiagram:
    tag_name: str
    tag_type: str
    total_count: int
    percentage: float
    total_amount: int
    avg_amount: float

@dataclass
class PieDiagramSegment:
    points: List[TagPieDiagram]
