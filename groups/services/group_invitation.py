from django.core.exceptions import ValidationError

from addition_info.choise_models import Status
from groups.models import GroupMembership


def create_group_invitation(list_of_connects: list[int],
                            group_id: int) -> None:
    existing = set(
        GroupMembership.objects.filter(
            group_id=group_id,
            user_id__in=list_of_connects
        ).values_list("user_id", flat=True)
    )

    GroupMembership.objects.bulk_create(
        [
            GroupMembership(group_id=group_id, user_id=user_id)
            for user_id in list_of_connects
            if user_id not in existing
        ]
    )


def accept_group_invitation(group_id: int, user_id: int) -> None:
    group = GroupMembership.objects.select_for_update().get(
        group_id=group_id,
        user_id=user_id
    )

    if not group:
        raise ValidationError("Group not found")

    group.status = Status.ACCEPTED
    group.save()


def reject_group_invitation(group_id: int, user_id: int) -> None:
    group = GroupMembership.objects.select_for_update().get(
        group_id=group_id,
        user_id=user_id
    )

    if not group:
        raise ValidationError("Group not found")

    group.delete()