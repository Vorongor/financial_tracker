import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from faker import Faker

from addition_info.choise_models import Role, Status
from groups.models import Group, \
    GroupMembership  # Заміни на свої назви додатків

User = get_user_model()


class Command(BaseCommand):
    help_tag = "Створює 100 груп та додає до них випадкових учасників"

    def handle(self, *args, **kwargs):
        fake = Faker(["uk_UA"])
        users = list(User.objects.all())

        if len(users) < 20:
            self.stdout.write(
                self.style.ERROR("Спочатку створи користувачів (seed_users)!"))
            return

        self.stdout.write("Починаємо створення груп...")

        try:
            with transaction.atomic():
                creators = random.sample(users, 100)

                for creator in creators:
                    group = Group.objects.create(
                        name=f"Група {fake.word().capitalize()} {fake.city()}",
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
                    "Успішно створено 100 груп та додано учасників!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Помилка: {e}"))
