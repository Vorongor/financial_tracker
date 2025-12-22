import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from faker import Faker
from events.models import Event, EventMembership

User = get_user_model()


class Command(BaseCommand):
    help = ("Creates private events for each user "
            "and 80 public events")

    def handle(self, *args, **kwargs):

        fake = Faker(["en_US"])
        users = list(User.objects.all())

        if not users:
            self.stdout.write(
                self.style.ERROR("Create users first!"))
            return

        self.stdout.write("Starting event generation...")

        try:
            with transaction.atomic():
                for user in users:
                    for _ in range(random.randint(1, 4)):
                        event = Event.objects.create(
                            name=f"Personal goal: {fake.word().capitalize()}",
                            description=fake.sentence(),
                            planned_amount=random.randint(1000, 50000),
                            event_type=random.choice(Event.EventType.choices)[
                                0],
                            status=random.choice(Event.EventStatus.choices)[0],
                            accessibility=Event.Accessibility.PRIVATE,
                            creator=user,
                            start_date=fake.date_this_year(),
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
                    event = Event.objects.create(
                        name=f"Public collection: {fake.bs().capitalize()}",
                        description=fake.paragraph(nb_sentences=2),
                        planned_amount=random.randint(50000, 500000),
                        event_type=random.choice(Event.EventType.choices)[0],
                        status=random.choice(Event.EventStatus.choices)[0],
                        accessibility=Event.Accessibility.PUBLIC,
                        creator=creator,
                        start_date=fake.date_this_year(),
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
