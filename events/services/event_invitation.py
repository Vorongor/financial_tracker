from django.core.exceptions import ValidationError

from addition_info.choise_models import Role, Status
from config import settings
from events.models import EventMembership, Event


class EventInvitationService:
    @classmethod
    def create_event_invitation(
            cls,
            list_of_connects: list[int],
            event_id: int
    ) -> None:
        if not list_of_connects:
            return

        existing = set(
            EventMembership.objects.filter(
                event_id=event_id, user_id__in=list_of_connects
            ).values_list("user_id", flat=True)
        )

        if len(list_of_connects) > 1:
            EventMembership.objects.bulk_create(
                [
                    EventMembership(event_id=event_id, user_id=user_id)
                    for user_id in list_of_connects
                    if user_id not in existing
                ]
            )
        else:
            EventMembership.objects.create(
                event_id=event_id,
                user_id=list_of_connects[0]
            )

    @classmethod
    def accept_event_invitation(cls, event_id: int, user_id: int) -> None:
        invitation = EventMembership.objects.get(
            event_id=event_id,
            user_id=user_id
        )
        if not invitation:
            return

        invitation.status = Status.ACCEPTED
        invitation.save()

    @classmethod
    def reject_event_invitation(cls, event_id: int, user_id: int) -> None:
        invitation = EventMembership.objects.get(
            event_id=event_id,
            user_id=user_id
        )
        if not invitation:
            # place for future Exception
            return

        invitation.delete()

    @classmethod
    def promote_member(cls, event_id: int, user_id: int) -> None:
        invitation = EventMembership.objects.get(event_id=event_id,
                                                 user_id=user_id)

        # place for future Exception/PermissionDenied

        invitation.role = Role.ADMIN
        invitation.save()

    @classmethod
    def leave_event(cls, event: Event, user: settings.AUTH_USER_MODEL) -> None:
        membership = EventMembership.objects.get(event=event, user=user)

        if membership.role == Role.CREATOR:
            raise ValidationError("Creator cannot leave")

        membership.delete()

        if not EventMembership.objects.filter(
                event=event).exists() and not event.creator:
            event.delete()
