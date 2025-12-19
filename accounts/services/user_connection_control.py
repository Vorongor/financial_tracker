from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q

from accounts.models import UserConnection

User = get_user_model()


def invite_user_to_connect(sender: User, recipient: User) -> None:
    if sender == recipient:
        raise ValidationError("You cannot connect to yourself.")

    existing = UserConnection.objects.filter(
        Q(from_user=sender, to_user=recipient) |
        Q(from_user=recipient, to_user=sender)
    ).first()

    if existing:
        if existing.status == UserConnection.Status.PENDING:
            raise ValidationError("Connection request already sent.")
        if existing.status == UserConnection.Status.ACCEPTED:
            raise ValidationError("You are already connected.")
        if existing.status == UserConnection.Status.BLOCKED:
            raise ValidationError("Connection was rejected.")

    UserConnection.objects.create(
        from_user=sender,
        to_user=recipient,
        status=UserConnection.Status.PENDING,
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