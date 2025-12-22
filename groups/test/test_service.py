from django.test import TestCase
from django.contrib.auth import get_user_model

from addition_info.choise_models import Status, Role
from groups.models import Group, GroupMembership, GroupEventConnection

from events.models import Event, EventMembership
from groups.services.group_event_service import GroupEventService
from groups.services.group_invitation import GroupInvitationService

User = get_user_model()


class GroupInvitationServiceTest(TestCase):
    def setUp(self):
        self.creator = get_user_model().objects.create_user(
            username="creator",
            password="pass"
        )
        self.user1 = get_user_model().objects.create_user(
            username="user1",
            password="pass"
        )
        self.user2 = get_user_model().objects.create_user(
            username="user2",
            password="pass"
        )
        self.group = Group.objects.create(
            name="Service Test Group",
            creator=self.creator
        )

    def test_create_group_invitation_bulk(self):
        user_ids = [self.user1.id, self.user2.id]

        GroupInvitationService.create_group_invitation(
            user_ids,
            self.group.id
        )
        self.assertEqual(
            GroupMembership.objects.filter(
                group=self.group
            ).count(), 2)

        GroupInvitationService.create_group_invitation(
            user_ids,
            self.group.id
        )
        self.assertEqual(
            GroupMembership.objects.filter(
                group=self.group
            ).count(), 2)

    def test_promote_demote_cycle(self):
        membership = GroupMembership.objects.create(
            group=self.group, user=self.user1, role=Role.MEMBER
        )

        GroupInvitationService.promote_group_member(
            self.group.id,
            self.user1.id
        )
        membership.refresh_from_db()
        self.assertEqual(membership.role, Role.MODERATOR)

        GroupInvitationService.promote_group_member(
            self.group.id,
            self.user1.id
        )
        membership.refresh_from_db()
        self.assertEqual(membership.role, Role.ADMIN)

        GroupInvitationService.demote_group_member(
            self.group.id,
            self.user1.id
        )
        membership.refresh_from_db()
        self.assertEqual(membership.role, Role.MODERATOR)

    def test_leave_group_creator_logic(self):
        GroupMembership.objects.create(
            group=self.group,
            user=self.creator
        )

        GroupInvitationService.leave_group(self.group.id, self.creator.id)

        self.group.refresh_from_db()
        self.assertIsNone(self.group.creator)
        self.assertFalse(
            GroupMembership.objects.filter(
                group=self.group,
                user=self.creator).exists()
        )


class GroupEventServiceTest(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="creator",
            password="1Qazcde3"
        )
        self.member = User.objects.create_user(
            username="member",
            password="1Qazcde3"
        )
        self.group = Group.objects.create(name="Event Group")

        GroupMembership.objects.create(
            group=self.group, user=self.member, status=Status.ACCEPTED
        )

        self.event = Event.objects.create(
            name="Group Trip",
            creator=self.creator,
            planned_amount=100
        )

    def test_invite_group_members_to_event(self):
        GroupEventService.invite_group_members_to_event(
            self.group,
            self.event
        )

        m_membership = EventMembership.objects.get(
            event=self.event,
            user=self.member
        )
        self.assertEqual(m_membership.status, Status.PENDING)

        c_membership = EventMembership.objects.get(
            event=self.event,
            user=self.creator
        )
        self.assertEqual(c_membership.status, Status.ACCEPTED)
        self.assertEqual(c_membership.role, Role.CREATOR)

    def test_create_group_event_connection(self):
        GroupEventService.create_group_event(self.group, self.event)

        self.assertTrue(GroupEventConnection.objects.filter(
            group=self.group,
            event=self.event
        ).exists())
