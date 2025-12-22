import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from accounts.models import UserConnection

User = get_user_model()


class Command(BaseCommand):
    help_tag = "Generates random connections (friendships) between users"

    def handle(self, *args, **kwargs):
        users = list(User.objects.all())
        if len(users) < 20:
            self.stdout.write(self.style.ERROR(
                "Not enough users to create connections!"))
            return

        self.stdout.write("Starting connection generation...")

        connections_to_create = []
        existing_pairs = set()

        for from_user in users:
            num_connections = random.randint(5, 15)

            candidates = random.sample(users,
                                       min(num_connections + 1, len(users)))

            for to_user in candidates:
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
                            )[0]
                        )
                    )

        try:
            UserConnection.objects.bulk_create(connections_to_create,
                                               batch_size=5000)
            self.stdout.write(self.style.SUCCESS(
                f"Successfully created {len(connections_to_create)} connections!"))
        except IntegrityError:
            self.stdout.write(self.style.ERROR(
                "Error: Attempting to create duplicates in the DB. "
                "Check the model's unique constraints."))
