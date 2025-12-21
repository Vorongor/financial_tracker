import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from faker import Faker
from events.models import Event, EventMembership

User = get_user_model()


class Command(BaseCommand):
    help = "Створює приватні події для кожного юзера та 150 публічних подій"

    def handle(self, *args, **kwargs):
        fake = Faker(['uk_UA'])
        users = list(User.objects.all())

        if not users:
            self.stdout.write(
                self.style.ERROR("Спочатку створи користувачів!"))
            return

        self.stdout.write("Починаємо генерацію подій...")

        try:
            with transaction.atomic():
                # --- 1. ПРИВАТНІ ПОДІЇ ---
                # Для кожного користувача створюємо 1-4 приватні події
                for user in users:
                    for _ in range(random.randint(1, 4)):
                        event = Event.objects.create(
                            name=f"Особиста ціль: {fake.word().capitalize()}",
                            description=fake.sentence(),
                            planned_amount=random.randint(1000, 50000),
                            type=random.choice(Event.EventType.choices)[0],
                            status=random.choice(Event.EventStatus.choices)[0],
                            accessibility=Event.Accessibility.PRIVATE,
                            creator=user,
                            start_date=fake.date_this_year(),
                        )
                        # Додаємо творця в учасники
                        EventMembership.objects.create(
                            event=event,
                            user=user,
                            role="Creator",
                            # Використовуй значення з твоєї моделі Role
                            status="Accepted"
                        )

                self.stdout.write(self.style.SUCCESS(
                    f"Створено приватні події для {len(users)} юзерів."))

                # --- 2. ПУБЛІЧНІ ПОДІЇ ---
                for i in range(80):
                    creator = random.choice(users)
                    event = Event.objects.create(
                        name=f"Публічний збір: {fake.bs().capitalize()}",
                        description=fake.paragraph(nb_sentences=2),
                        planned_amount=random.randint(50000, 500000),
                        type=random.choice(Event.EventType.choices)[0],
                        status=random.choice(Event.EventStatus.choices)[0],
                        accessibility=Event.Accessibility.PUBLIC,
                        creator=creator,
                        start_date=fake.date_this_year(),
                    )

                    # Додаємо творця
                    EventMembership.objects.create(
                        event=event,
                        user=creator,
                        role="Creator",
                        status="Accepted"
                    )

                    # Додаємо від 5 до 15 випадкових учасників
                    num_members = random.randint(5, 15)
                    selected_users = random.sample(users, num_members)
                    for member in selected_users:
                        if member != creator:
                            EventMembership.objects.create(
                                event=event,
                                user=member,
                                role="Member",
                                status="Accepted"
                            )

                self.stdout.write(self.style.SUCCESS(
                    "Успішно створено 80 публічних подій з учасниками!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Помилка: {e}"))
