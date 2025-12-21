from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from addition_info.choise_models import Status, Role
from groups.models import Group, GroupMembership
from finances.models import Budget
from unittest.mock import patch

User = get_user_model()


class GroupsViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="1Qazcde3"
        )
        self.friend = User.objects.create_user(
            username="friend",
            password="1Qazcde3"
        )
        self.client.login(
            username="testuser",
            password="1Qazcde3"
        )

        self.group = Group.objects.create(name="My Group", creator=self.user)
        self.membership = GroupMembership.objects.create(
            group=self.group,
            user=self.user,
            status=Status.ACCEPTED,
            role=Role.CREATOR
        )

    def test_groups_home_view_context(self):
        other_group = Group.objects.create(name="Other Group")
        GroupMembership.objects.create(
            group=other_group,
            user=self.user,
            status=Status.PENDING
        )

        response = self.client.get(reverse("groups:home"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.group, response.context["groups"])
        self.assertEqual(len(response.context["invites"]), 1)

    @patch(
        "groups.services.group_invitation.GroupInvitationService.create_group_invitation")
    @patch(
        "accounts.services.receive_connection.UserConnectionsService.get_user_connections")
    def test_group_create_post(self, mock_connections, mock_invite_service):
        mock_connections.return_value = []
        url = reverse("groups:create")
        data = {
            "name": "Brand New Group",
            "state": Group.States.PERMANENT,
            "participants": []
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        new_group = Group.objects.get(name="Brand New Group")
        self.assertEqual(new_group.creator, self.user)
        self.assertTrue(
            GroupMembership.objects.filter(
                group=new_group,
                user=self.user,
                role=Role.CREATOR
            ).exists()
        )

    def test_promote_member_view(self):
        member_user = User.objects.create_user(
            username="member",
            password="password"
        )
        membership = GroupMembership.objects.create(
            group=self.group,
            user=member_user,
            status=Status.ACCEPTED,
            role=Role.MEMBER
        )

        url = reverse(
            "groups:promote",
            kwargs={"pk": self.group.pk, "user_id": member_user.id}
        )
        response = self.client.post(url)

        membership.refresh_from_db()
        self.assertEqual(membership.role, Role.MODERATOR)
        self.assertRedirects(
            response, reverse(
                "groups:detail",
                kwargs={"pk": self.group.pk}
            )
        )

    def test_create_event_inside_group_denied_for_non_members(self):
        intruder = User.objects.create_user(
            username="intruder",
            password="password")

        self.client.login(
            username="intruder",
            password="password"
        )

        url = reverse(
            "groups:create-inside-event",
            kwargs={"group_id": self.group.id}
        )

        with self.assertRaises(Exception):
            self.client.get(url)

    def test_group_edit_post(self):
        budget = Budget.objects.get(
            content_type=ContentType.objects.get_for_model(Group),
            object_id=self.group.id,
        )
        budget.planned_amount = 100
        budget.save()

        url = reverse("groups:update", kwargs={"pk": self.group.pk})
        data = {
            "name": "Updated Group Name",
            "state": Group.States.PERMANENT,
            "planned_amount": 999,
            "start_amount": 0
        }
        response = self.client.post(url, data)

        self.group.refresh_from_db()
        budget.refresh_from_db()
        self.assertEqual(self.group.name, "Updated Group Name")
        self.assertEqual(budget.planned_amount, 999)

    def test_leave_group_view(self):
        url = reverse(
            "groups:leave-group",
            kwargs={"group_id": self.group.id}
        )
        response = self.client.post(url)

        self.assertFalse(GroupMembership.objects.filter(
            group=self.group,
            user=self.user).exists()
                         )
        self.assertRedirects(response, reverse("groups:home"))
