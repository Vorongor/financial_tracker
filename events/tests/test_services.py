from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from events.models import Event, EventMembership
from addition_info.choise_models import Role, Status
from events.services.event_invitation import EventInvitationService

User = get_user_model()


class TestEventInvitationService(TestCase):
    def setUp(self):
        self.creator = User.objects.create(
            username="creator",
            email="c@test.com"
        )
        self.user1 = User.objects.create(
            username="user1",
            email="u1@test.com"
        )
        self.user2 = User.objects.create(
            username="user2",
            email="u2@test.com"
        )

        self.event = Event.objects.create(
            name="Test Event",
            creator=self.creator,
        )

    def test_create_event_invitation_bulk(self):
        user_ids = [self.user1.id, self.user2.id]

        EventInvitationService.create_event_invitation(
            user_ids,
            self.event.id
        )

        memberships = EventMembership.objects.filter(
            event_id=self.event.id,
            user_id__in=user_ids
        )
        self.assertEqual(memberships.count(), 2)

    def test_create_event_invitation_already_exists(self):
        EventMembership.objects.create(
            event=self.event,
            user=self.user1
        )

        user_ids = [self.user1.id, self.user2.id]
        EventInvitationService.create_event_invitation(
            user_ids,
            self.event.id
        )

        self.assertEqual(
            EventMembership.objects.filter(
                event=self.event
            ).count(), 2)

    def test_accept_event_invitation(self):
        membership = EventMembership.objects.create(
            event=self.event,
            user=self.user1,
            status=Status.PENDING
        )

        EventInvitationService.accept_event_invitation(
            self.event.id,
            self.user1.id
        )

        membership.refresh_from_db()
        self.assertEqual(membership.status, Status.ACCEPTED)

    def test_reject_event_invitation(self):
        EventMembership.objects.create(
            event=self.event,
            user=self.user1
        )

        EventInvitationService.reject_event_invitation(
            self.event.id,
            self.user1.id
        )

        self.assertFalse(EventMembership.objects.filter(
            event=self.event,
            user=self.user1
        ).exists())

    def test_promote_member(self):
        membership = EventMembership.objects.create(
            event=self.event,
            user=self.user1,
            role=Role.MEMBER
        )

        EventInvitationService.promote_member(self.event.id, self.user1.id)

        membership.refresh_from_db()
        self.assertEqual(membership.role, Role.ADMIN)

    def test_leave_event_creator_fails(self):
        membership = EventMembership.objects.create(
            event=self.event,
            user=self.creator,
            role=Role.CREATOR
        )

        with self.assertRaises(ValidationError) as cm:
            EventInvitationService.leave_event(self.event, self.creator)

        self.assertEqual(cm.exception.message, "Creator cannot leave")

    def test_leave_event_member_success(self):
        membership = EventMembership.objects.create(
            event=self.event,
            user=self.user1,
            role=Role.MEMBER
        )

        EventInvitationService.leave_event(self.event, self.user1)
        self.assertFalse(
            EventMembership.objects.filter(id=membership.id).exists()
        )

    def test_leave_event_delete_event_if_empty(self):
        event_without_creator = Event.objects.create(
            name="Ghost Event",
            creator=None
        )
        membership = EventMembership.objects.create(
            event=event_without_creator,
            user=self.user1,
            role=Role.MEMBER
        )

        EventInvitationService.leave_event(event_without_creator, self.user1)

        self.assertFalse(
            Event.objects.filter(id=event_without_creator.id).exists())
