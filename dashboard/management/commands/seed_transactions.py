import random
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from finances.models import Transaction, Budget, Category
from finances.services.transfers_service import TransfersService
from groups.models import Group
from events.models import Event

User = get_user_model()


class Command(BaseCommand):
    help_tag = "Generates an array of transactions for the last six months"

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
        expense_cats = list(
            Category.objects.filter(category_type=Category.Types.EXPENSE))

        now = timezone.now()
        half_year_ago = 180

        def get_random_aware_datetime(days_back):
            naive_date = now.date() - timedelta(days=days_back)
            naive_datetime = datetime.combine(naive_date, time.min)
            return timezone.make_aware(naive_datetime)

        self.stdout.write(
            f"Starting generation for the last {half_year_ago} days...")

        try:
            with transaction.atomic():

                self.stdout.write("Generating incomes...")
                for user in users:
                    budget = user_budgets.get(user.id)
                    if not budget:
                        continue
                    for month_offset in range(6):
                        days_back = (month_offset * 30) + random.randint(0, 5)
                        TransfersService.top_up_budget(
                            user=user,
                            amount=Decimal(
                                random.randint(20000, 45000)
                            ),
                            category=random.choice(income_cats),
                            date=get_random_aware_datetime(days_back),
                            note="Monthly Salary"
                        )

                self.stdout.write("Generating personal expenses...")
                for user in users:
                    budget = user_budgets.get(user.id)
                    if not budget:
                        continue
                    for _ in range(random.randint(40, 60)):
                        TransfersService.set_expense(
                            user=user,
                            amount=Decimal
                            (random.randint(150, 3000)
                             ),
                            category=random.choice(expense_cats),
                            date=get_random_aware_datetime(
                                random.randint(0, half_year_ago)
                            ),
                            note="Daily expense"
                        )
                    budget.recalc()

                self.stdout.write("Generating contributions to groups...")
                for group in Group.objects.all():
                    target_budget = group_budgets.get(group.id)
                    if not target_budget:
                        continue
                    memberships = group.groupslink.filter(status="Accepted")[
                        :5]
                    for ms in memberships:
                        payer_budget = user_budgets.get(ms.user.id)
                        if not payer_budget:
                            continue
                        for _ in range(random.randint(3, 5)):
                            TransfersService.transfer_between_budgets(
                                amount=Decimal(
                                    random.randint(1000, 4000)
                                ),
                                from_budget=payer_budget,
                                to_budget=target_budget,
                                payer=ms.user,
                                date=get_random_aware_datetime(
                                    random.randint(0, half_year_ago)
                                ),
                                note=f"Membership fee for {group.name}"
                            )

                self.stdout.write("Generating contributions to events...")
                for event in Event.objects.all():
                    target_budget = event_budgets.get(event.id)
                    if not target_budget:
                        continue
                    memberships = event.memberships.filter(status="Accepted")[
                        :5]
                    for ms in memberships:
                        payer_budget = user_budgets.get(ms.user.id)
                        if not payer_budget:
                            continue
                        for _ in range(random.randint(3, 5)):
                            TransfersService.transfer_between_budgets(
                                amount=Decimal(
                                    random.randint(500, 2000)
                                ),
                                from_budget=payer_budget,
                                to_budget=target_budget,
                                payer=ms.user,
                                date=get_random_aware_datetime(
                                    random.randint(0, half_year_ago)
                                ),
                                note=f"Support for event: {event.name}"
                            )

            self.stdout.write(
                self.style.SUCCESS("Done! Data generated successfully."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
