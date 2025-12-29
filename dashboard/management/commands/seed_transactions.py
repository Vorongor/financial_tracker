import random
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from finances.models import Transaction, Budget, Category
from groups.models import Group
from events.models import Event

User = get_user_model()


class Command(BaseCommand):
    help = "Generates transactions for users with optimized bulk creation"

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        user_type = ContentType.objects.get_for_model(User)
        group_type = ContentType.objects.get_for_model(Group)
        event_type = ContentType.objects.get_for_model(Event)

        user_budgets = {b.object_id: b for b in
                        Budget.objects.filter(content_type=user_type)}
        group_budgets = {b.object_id: b for b in
                         Budget.objects.filter(content_type=group_type)}
        event_budgets = {b.object_id: b for b in
                         Budget.objects.filter(content_type=event_type)}

        income_cats = list(Category.objects.filter(category_type=Category.Types.INCOME))
        expense_cats = list(Category.objects.filter(category_type=Category.Types.EXPENSE))

        now = timezone.now()
        days_range = 60  # зменшено з 180 на 60 днів

        def random_date(days_back):
            date = now - timedelta(days=days_back)
            return timezone.make_aware(datetime.combine(date.date(), time.min))

        self.stdout.write(f"Starting generation for the last {days_range} days...")

        for i, user in enumerate(users, 1):
            budget = user_budgets.get(user.id)
            if not budget:
                continue

            self.stdout.write(f"[{i}/{users.count()}] Generating transactions for user {user.username}...")

            transactions_to_create = []

            # Генеруємо incomes (щомісячна зарплата)
            for month_offset in range(2):  # 2 місяці для тесту, можна 6
                days_back = month_offset * 30 + random.randint(0, 5)
                transactions_to_create.append(Transaction(
                    amount=Decimal(random.randint(20000, 45000)),
                    transaction_type=Transaction.Types.INCOME,
                    date=random_date(days_back),
                    target=budget,
                    payer=user,
                    category=random.choice(income_cats),
                    note="Monthly Salary"
                ))

            # Генеруємо персональні витрати
            for _ in range(random.randint(10, 20)):  # зменшено з 40-60
                transactions_to_create.append(Transaction(
                    amount=Decimal(random.randint(150, 3000)),
                    transaction_type=Transaction.Types.EXPENSE,
                    date=random_date(random.randint(0, days_range)),
                    target=budget,
                    payer=user,
                    category=random.choice(expense_cats),
                    note="Daily expense"
                ))

            # Bulk create для користувача
            with transaction.atomic():
                Transaction.objects.bulk_create(transactions_to_create)
                budget.recalc()

            self.stdout.write(f"  Created {len(transactions_to_create)} transactions for {user.username}")

        # Генерація внесків до груп
        self.stdout.write("Generating contributions to groups...")
        for group in Group.objects.all():
            target_budget = group.budget
            if not target_budget:
                continue
            memberships = group.memberships.filter(status="Accepted")[:5]
            for ms in memberships:
                payer_budget = user_budgets.get(ms.user.id)
                if not payer_budget:
                    continue
                transactions_to_create = []
                for _ in range(random.randint(3, 5)):
                    category = random.choice(income_cats + expense_cats)
                    transactions_to_create.append(Transaction(
                        amount=Decimal(random.randint(1000, 4000)),
                        transaction_type=Transaction.Types.EXPENSE,
                        date=random_date(random.randint(0, days_range)),
                        target=target_budget,
                        payer=ms.user,
                        category=category,
                        note=f"Membership fee for {group.name}"
                    ))
                Transaction.objects.bulk_create(transactions_to_create)
                target_budget.recalc()

        #Генерація внесків до подій
        self.stdout.write("Generating contributions to events...")
        for event in Event.objects.all():
            target_budget = event_budgets.get(event.id)
            if not target_budget:
                continue
            memberships = event.memberships.filter(status="Accepted")[:5]
            for ms in memberships:
                payer_budget = user_budgets.get(ms.user.id)
                if not payer_budget:
                    continue
                transactions_to_create = []
                for _ in range(random.randint(3, 5)):
                    if event.event_type == Event.EventType.ACCUMULATIVE:
                        category = random.choice(income_cats)
                        t_type = Transaction.Types.INCOME
                    elif event.event_type == Event.EventType.EXPENSES:
                        category = random.choice(expense_cats)
                        t_type = Transaction.Types.EXPENSE
                    else:
                        category = random.choice(income_cats + expense_cats)
                        t_type = random.choice([Transaction.Types.INCOME, Transaction.Types.EXPENSE])

                    transactions_to_create.append(Transaction(
                        amount=Decimal(random.randint(500, 2000)),
                        transaction_type=t_type,
                        date=random_date(random.randint(0, days_range)),
                        target=target_budget,
                        payer=ms.user,
                        category=category,
                        note=f"Support for event: {event.name}"
                    ))
                Transaction.objects.bulk_create(transactions_to_create)
                target_budget.recalc()

        self.stdout.write(self.style.SUCCESS("Done! All transactions generated successfully."))
