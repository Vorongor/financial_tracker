import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from faker import Faker

from addition_info.choise_models import Role, Status
from groups.models import Group, GroupMembership

User = get_user_model()


class Command(BaseCommand):
    help_tag = "Creates 100 groups and adds random members to them"

    def handle(self, *args, **kwargs):
        fake = Faker(["en_US"])
        users = list(User.objects.all())

        if len(users) < 20:
            self.stdout.write(
                self.style.ERROR("Please create users first (seed_users)!"))
            return

        self.stdout.write("Starting the group creation process...")

        try:
            with transaction.atomic():
                # Note: This logic assumes you have at least 100 users if you want 100 unique creators.
                # If users < 100, use random.choices or reduce the count.
                creators = random.sample(users, 100)

                for creator in creators:
                    group = Group.objects.create(
                        name=f"Group {fake.word().capitalize()} {fake.city()}",
                        description=fake.text(max_nb_chars=200),
                        state=random.choice(Group.States.choices)[0],
                        creator=creator,
                        start_date=fake.date_this_year(),
                    )

                    GroupMembership.objects.create(
                        group=group,
                        user=creator,
                        role=Role.CREATOR,
                        status=Status.ACCEPTED
                    )

                    potential_members = [u for u in users if u != creator]
                    num_members = random.randint(3, 10)
                    selected_users = random.sample(potential_members,
                                                   num_members)

                    for member in selected_users:
                        GroupMembership.objects.create(
                            group=group,
                            user=member,
                            role=random.choice([
                                Role.ADMIN,
                                Role.MODERATOR,
                                Role.MEMBER
                            ]),
                            status=Status.ACCEPTED
                        )

                self.stdout.write(self.style.SUCCESS(
                    "Successfully created 100 groups and added members!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error occurred: {e}"))