from django.db import transaction
from decimal import Decimal

from finances.models import Transaction, Category


@transaction.atomic
def transfer_between_budgets(
    *,
    amount: Decimal,
    from_budget,
    to_budget,
    payer,
    date,
    note="",
    category=None,
):
    """
    Atomic transfer: creates 2 transactions
    """

    # 1. EXPENSE from payer budget
    Transaction.objects.create(
        amount=amount,
        type=Transaction.Types.EXPENSE,
        target=from_budget,
        payer=payer,
        date=date,
        category=category,
        note=note,
    )

    # 2. INCOME to target budget
    Transaction.objects.create(
        amount=amount,
        type=Transaction.Types.INCOME,
        target=to_budget,
        payer=payer,
        date=date,
        category=category,
        note=note,
    )

    # 3. Recalc both budgets
    from_budget.recalc()
    to_budget.recalc()
