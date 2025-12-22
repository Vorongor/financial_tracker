import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from accounts.models import UserConnection

User = get_user_model()


class Command(BaseCommand):
    help_tag = "Генерує випадкові зв'язки (дружбу) між користувачами"

    def handle(self, *args, **kwargs):
        users = list(User.objects.all())
        if len(users) < 20:
            self.stdout.write(self.style.ERROR(
                "Недостатньо користувачів для створення зв'язків!"))
            return

        self.stdout.write("Починаємо генерацію зв'язків...")

        connections_to_create = []
        existing_pairs = set()  # Для уникнення дублікатів {(id1, id2), ...}

        for from_user in users:
            # Кожен юзер має від 5 до 15 зв'язків
            num_connections = random.randint(5, 15)

            # Вибираємо випадкових кандидатів
            candidates = random.sample(users,
                                       min(num_connections + 1, len(users)))

            for to_user in candidates:
                # 1. Не можна підписуватися на самого себе
                # 2. Не створюємо дублікат зв'язку в межах цього скрипта
                pair = tuple(sorted((from_user.id, to_user.id)))

                if from_user != to_user and pair not in existing_pairs:
                    existing_pairs.add(pair)

                    connections_to_create.append(
                        UserConnection(
                            from_user=from_user,
                            to_user=to_user,
                            status=random.choices(
                                [UserConnection.Status.ACCEPTED,
                                 UserConnection.Status.PENDING,
                                 UserConnection.Status.BLOCKED],
                                weights=[0.7, 0.2, 0.1]
                                # Більшість зв'язків "Прийняті"
                            )[0]
                        )
                    )

        # Використовуємо bulk_create для швидкого запису в базу
        # batch_size=5000 допоможе, якщо зв'язків буде дуже багато
        try:
            UserConnection.objects.bulk_create(connections_to_create,
                                               batch_size=5000)
            self.stdout.write(self.style.SUCCESS(
                f"Успішно створено {len(connections_to_create)} зв'язків!"))
        except IntegrityError:
            self.stdout.write(self.style.ERROR(
                "Помилка: Спроба створити дублікати в БД. "
                "Перевір унікальні обмеження моделі."))
