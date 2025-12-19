from addition_info.choise_models import Status, Role
from events.models import Event, EventMembership
from groups.models import GroupEventConnection, Group, GroupMembership


def invite_group_members_to_event(group: Group, event: Event):
    members = GroupMembership.objects.filter(
        group=group, status=Status.ACCEPTED
    ).exclude(user=event.creator)

    EventMembership.objects.bulk_create(
        [
            EventMembership(event=event, user=membership.user, status=Status.PENDING)
            for membership in members
        ],
        ignore_conflicts=True,
    )
    membership, _ = EventMembership.objects.get_or_create(
        event=event,
        user=event.creator,
    )
    membership.status = Status.ACCEPTED
    membership.role = Role.CREATOR
    membership.save()


def create_group_event(*, group, event):
    GroupEventConnection.objects.create(group=group, event=event)

    invite_group_members_to_event(group, event)

    return event


def get_events_for_group(group_id: int):
    events = GroupEventConnection.objects.filter(group=group_id).all()
    return events
