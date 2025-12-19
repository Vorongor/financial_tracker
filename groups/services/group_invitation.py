from django.core.exceptions import ValidationError

from addition_info.choise_models import Status, Role
from groups.models import GroupMembership, Group


def create_group_invitation(list_of_connects: list[int], group_id: int) -> None:
    existing = set(
        GroupMembership.objects.filter(
            group_id=group_id, user_id__in=list_of_connects
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
        group_id=group_id, user_id=user_id
    )

    if not group:
        raise ValidationError("Group not found")

    group.status = Status.ACCEPTED
    group.save()


def reject_group_invitation(group_id: int, user_id: int) -> None:
    group = GroupMembership.objects.select_for_update().get(
        group_id=group_id, user_id=user_id
    )

    if not group:
        raise ValidationError("Group not found")

    group.delete()


def promote_group_member(group_id: int, user_id: int) -> None:
    group = GroupMembership.objects.select_for_update().get(
        group_id=group_id, user_id=user_id
    )
    if not group:
        raise ValidationError("Group not found")

    if group.role == Role.MEMBER:
        group.role = Role.MODERATOR
        group.save()
    elif group.role == Role.MODERATOR:
        group.role = Role.ADMIN
        group.save()
    else:
        return


def demote_group_member(group_id: int, user_id: int) -> None:
    group = GroupMembership.objects.select_for_update().get(
        group_id=group_id, user_id=user_id
    )
    if not group:
        raise ValidationError("Group not found")

    if group.role == Role.MODERATOR:
        group.role = Role.MEMBER
        group.save()
    elif group.role == Role.ADMIN:
        group.role = Role.MODERATOR
        group.save()
    else:
        return


def leave_group(group_id: int, user_id: int) -> None:
    group_membership = GroupMembership.objects.select_for_update().get(
        group_id=group_id, user_id=user_id
    )

    if group_membership:
        group_membership.delete()

    group = Group.objects.select_for_update().get(pk=group_id)

    if not group:
        raise ValidationError("Group not found")

    if group.creator_id == user_id:
        group.creator = None
        group.save()

    if not group.creator and not group_membership:
        group.delete()
