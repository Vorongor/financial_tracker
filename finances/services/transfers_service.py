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

        return owner.budget

    @classmethod
    @transaction.atomic
    def transfer_between_budgets(
            cls,
            amount: Decimal,
            from_budget: Budget,
            to_budget: Budget,
            payer: User,
            date,
            category: Category,
            note: str = "",
    ) -> None:
        Transaction.objects.create(
            amount=amount,
            transaction_type=category.category_type,
            target=from_budget,
            payer=payer,
            date=date,
            category=category,
            note=note,
        )
        Transaction.objects.create(
            amount=amount,
            transaction_type=category.category_type,
            target=to_budget,
            payer=payer,
            date=date,
            category=category,
            note=note,
        )

        from_budget.recalc()
        to_budget.recalc()

    @classmethod
    @transaction.atomic
    def top_up_budget(
            cls,
            user: User,
            amount: Decimal,
            category: Category = None,
            note: str = "",
            date=timezone.now().date()
    ) -> Transaction:
        if category is None:
            category, _ = Category.objects.get_or_create(
                name="Top Up",
                category_type=Category.Types.INCOME,
                color_hex="#00ff00",
            )
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
    def set_expense(
            cls,
            user: User,
            amount: Decimal,
            category=None,
            note: str = "",
            date=timezone.now().date()
    ) -> Transaction:
        if category is None:
            category, _ = Category.objects.get_or_create(
                name="Other expense",
                category_type=Category.Types.EXPENSE,
                color_hex="#ff0000",
            )
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
