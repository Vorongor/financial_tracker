from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone

from events.models import Event
from finances.models import Transaction, Category, Budget
from groups.models import Group

User = get_user_model()


class TransfersService:
    @classmethod
    def get_budget_by_content_type(
            cls,
            content_type: str,
            object_id: int
    ) -> Budget:
        owner_models = {
            "event": Event,
            "group": Group,
            "user": User,
        }
        model = owner_models.get(content_type)
        if not model:
            raise ValueError(f"Invalid owner type: {content_type}")

        owner = get_object_or_404(model, pk=object_id)
        if not hasattr(owner, "budget") or not owner.budget:
            raise ValueError("Target has no budget")

        return owner.budget

    @classmethod
    @transaction.atomic
    def transfer_between_budgets(cls,
                                 amount: Decimal,
                                 from_budget: Budget,
                                 to_budget: Budget,
                                 payer: User,
                                 date,
                                 note: str = "",
                                 category: Category = None,
                                 ) -> None:
        donate = Category.objects.get(
            name="Spent on donate"
        )
        receive = Category.objects.get(
            name="Receive from saved"
        )
        expense_category = category if (
            category
            and category.category_type == Category.Types.EXPENSE
        ) else donate

        income_category = category if (
            category
            and category.category_type == Category.Types.INCOME
        ) else receive

        # 1. EXPENSE from payer budget
        Transaction.objects.create(
            amount=amount,
            transaction_type=Transaction.Types.EXPENSE,
            target=from_budget,
            payer=payer,
            date=date,
            category=expense_category,
            note=note,
        )

        # 2. INCOME to target budget
        Transaction.objects.create(
            amount=amount,
            transaction_type=Transaction.Types.INCOME,
            target=to_budget,
            payer=payer,
            date=date,
            category=income_category,
            note=note,
        )

        from_budget.recalc()
        to_budget.recalc()

    @classmethod
    @transaction.atomic
    def top_up_budget(cls,
                      user: User,
                      amount: Decimal,
                      category: Category = None,
                      note: str = "",
                      date=timezone.now().date()
                      ):
        transaction = Transaction.objects.create(
            amount=amount,
            transaction_type=Transaction.Types.INCOME,
            target=user.budget,
            payer=user,
            date=date,
            category=category,
            note=note,
        )
        user.budget.recalc()
        return transaction

    @classmethod
    @transaction.atomic
    def set_expense(cls,
                    user: User,
                    amount: Decimal,
                    category=None,
                    note: str = "",
                    date=timezone.now().date()
                    ) -> Transaction:
        transaction = Transaction.objects.create(
            amount=amount,
            transaction_type=Transaction.Types.EXPENSE,
            target=user.budget,
            payer=user,
            date=date,
            category=category,
            note=note,
        )
        user.budget.recalc()
        return transaction
