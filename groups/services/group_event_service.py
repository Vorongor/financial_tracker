from django.db.models import QuerySet

from addition_info.choise_models import Status, Role
from events.models import Event, EventMembership
from groups.models import GroupEventConnection, Group, GroupMembership


class GroupEventService:
    @classmethod
    def invite_group_members_to_event(cls, group: Group, event: Event) -> None:
        members = GroupMembership.objects.filter(
            group=group, status=Status.ACCEPTED
        ).exclude(user=event.creator)

        EventMembership.objects.bulk_create(
            [
                EventMembership(
                    event=event,
                    user=membership.user,
                    status=Status.PENDING)
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

    @classmethod
    def create_group_event(cls, group, event) -> Event:
        GroupEventConnection.objects.create(group=group, event=event)

        cls.invite_group_members_to_event(group, event)

        return event

    @classmethod
    def get_events_for_group(
            cls,
            group_id: int
    ) -> QuerySet[GroupEventConnection]:
        events = GroupEventConnection.objects.filter(group=group_id).all()
        return events
