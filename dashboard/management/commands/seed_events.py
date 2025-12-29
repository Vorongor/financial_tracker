import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from faker import Faker
from events.models import Event, EventMembership
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = ("Creates private events for each user "
            "and 80 public events")

    def handle(self, *args, **kwargs):

        fake = Faker(["en_US"])
        users = list(User.objects.all())

        def generate_valid_dates():
            start = fake.date_between_dates(
                date_start=timezone.now().date() - timedelta(days=60),
                date_end=timezone.now().date() + timedelta(days=30),
            )
            end = fake.date_between_dates(
                date_start=start,
                date_end=start + timedelta(days=365),
            )
            return start, end

        if not users:
            self.stdout.write(
                self.style.ERROR("Create users first!"))
            return

        self.stdout.write("Starting event generation...")

        try:
            with transaction.atomic():
                for user in users:
                    for _ in range(random.randint(1, 4)):
                        event_type = random.choice(Event.EventType.choices)[0]

                        # planned amount always > 0
                        planned_amount = random.randint(1, 500000)

                        # Dates depend on event type
                        if event_type in [
                            Event.EventType.EXPENSES,
                            Event.EventType.ACCUMULATIVE
                        ]:
                            start_date, end_date = generate_valid_dates()
                        else:
                            start_date = fake.date_this_year()
                            end_date = None

                        event = Event.objects.create(
                            name=fake.sentence(nb_words=3),
                            description=fake.text(),
                            planned_amount=planned_amount,
                            event_type=event_type,
                            status=random.choice(Event.EventStatus.choices)[0],
                            accessibility=Event.Accessibility.PRIVATE,
                            # or PUBLIC in second block
                            creator=user,
                            start_date=start_date,
                            end_date=end_date,
                        )
                        EventMembership.objects.create(
                            event=event,
                            user=user,
                            role="Creator",
                            status="Accepted"
                        )

                self.stdout.write(self.style.SUCCESS(
                    f"Created private events for {len(users)} users."))

                # Generate Public Events
                for i in range(80):
                    creator = random.choice(users)
                    event_type = random.choice(Event.EventType.choices)[0]

                    # planned amount always > 0
                    planned_amount = random.randint(1, 50000)

                    # Dates depend on event type
                    if event_type in [
                        Event.EventType.EXPENSES,
                        Event.EventType.ACCUMULATIVE
                    ]:
                        start_date, end_date = generate_valid_dates()
                    else:
                        start_date = fake.date_this_year()
                        end_date = None

                    event = Event.objects.create(
                        name=fake.sentence(nb_words=3),
                        description=fake.text(),
                        planned_amount=planned_amount,
                        event_type=event_type,
                        status=random.choice(Event.EventStatus.choices)[0],
                        accessibility=Event.Accessibility.PUBLIC,
                        creator=user,
                        start_date=start_date,
                        end_date=end_date,
                    )

                    EventMembership.objects.create(
                        event=event,
                        user=creator,
                        role="Creator",
                        status="Accepted"
                    )

                    num_members = random.randint(5, 15)
                    selected_users = random.sample(users, min(len(users),
                                                              num_members))
                    for member in selected_users:
                        if member != creator:
                            EventMembership.objects.create(
                                event=event,
                                user=member,
                                role="Member",
                                status="Accepted"
                            )

                self.stdout.write(self.style.SUCCESS(
                    "Successfully created 80 public events with participants!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
