from django.contrib.auth import get_user_model

from accounts.models import UserConnection

User = get_user_model()


def invite_user_to_connect(sender: User, recipient: User) -> None:
    UserConnection.objects.get_or_create(
        from_user=sender,
        to_user=recipient,
        defaults={"status": UserConnection.Status.PENDING},
    )

def approve_user_to_connect(connection_id: int) -> None:
    connection = UserConnection.objects.get(pk=connection_id)
    connection.status = UserConnection.Status.ACCEPTED
    connection.save()


def reject_user_to_connect(connection_id: int) -> None:
    UserConnection.objects.get(pk=connection_id).delete()


def block_user_to_connect(connection_id: int) -> None:
    connection = UserConnection.objects.get(pk=connection_id)
    connection.status = UserConnection.Status.BLOCKED
    connection.save()