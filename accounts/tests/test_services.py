from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.http import Http404
from django.core.exceptions import ValidationError
from accounts.models import UserConnection
from accounts.services.receive_connection import UserConnectionsService
from accounts.services.user_budget_service import UserBudgetService
from accounts.services.user_connection_control import UserInvitationService
from finances.models import Budget

User = get_user_model()


class UserConnectionsServiceTest(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username="u1")
        self.u2 = User.objects.create_user(username="u2")
        self.u3 = User.objects.create_user(username="u3")

        self.conn_accepted = UserConnection.objects.create(
            from_user=self.u1, to_user=self.u2,
            status=UserConnection.Status.ACCEPTED
        )
        self.conn_pending = UserConnection.objects.create(
            from_user=self.u3, to_user=self.u1,
            status=UserConnection.Status.PENDING
        )

    def test_get_user_connections_all(self):
        connections = UserConnectionsService.get_user_connections(self.u1.id)
        self.assertEqual(connections.count(), 2)
        self.assertIn(self.conn_accepted, connections)
        self.assertIn(self.conn_pending, connections)

    def test_get_user_connections_filtered_by_status(self):
        accepted = UserConnectionsService.get_user_connections(
            self.u1.id,
            status=UserConnection.Status.ACCEPTED
        )
        self.assertEqual(accepted.count(), 1)
        self.assertEqual(accepted.first(), self.conn_accepted)

    def test_get_user_from_uk_success(self):
        result = UserConnectionsService.get_user_from_uk(
            str(self.u1.connect_key))
        self.assertEqual(result, self.u1)

    def test_get_user_from_uk_404(self):
        with self.assertRaises(Http404):
            UserConnectionsService.get_user_from_uk("non-existent-uuid")


class UserInvitationServiceTest(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(username="sender")
        self.receiver = User.objects.create_user(username="receiver")

    def test_invite_user_success(self):
        UserInvitationService.invite_user_to_connect(
            self.sender,
            self.receiver
        )
        self.assertTrue(UserConnection.objects.filter(
            from_user=self.sender,
            to_user=self.receiver,
            status="Pending"
        ).exists())

    def test_invite_self_raises_error(self):
        with self.assertRaisesMessage(
                ValidationError,
                "You cannot connect to yourself."
        ):
            UserInvitationService.invite_user_to_connect(
                self.sender,
                self.sender
            )

    def test_invite_existing_connection_raises_error(self):
        UserConnection.objects.create(
            from_user=self.sender,
            to_user=self.receiver,
            status="Accepted"
        )
        with self.assertRaisesMessage(
                ValidationError,
                "You are already connected."
        ):
            UserInvitationService.invite_user_to_connect(
                self.sender,
                self.receiver
            )

    def test_approve_invitation(self):
        conn = UserConnection.objects.create(
            from_user=self.sender,
            to_user=self.receiver
        )
        UserInvitationService.approve_user_to_connect(conn.id)
        conn.refresh_from_db()
        self.assertEqual(conn.status, UserConnection.Status.ACCEPTED)

    def test_reject_invitation_deletes_record(self):
        conn = UserConnection.objects.create(
            from_user=self.sender,
            to_user=self.receiver
        )
        UserInvitationService.reject_user_to_connect(conn.id)
        self.assertFalse(UserConnection.objects.filter(
            id=conn.id
        ).exists())


class UserBudgetServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="budget_user")
        self.ct = ContentType.objects.get_for_model(self.user)

        self.budget, _ = Budget.objects.get_or_create(
            content_type=self.ct,
            object_id=self.user.id,
        )

    def test_get_budget_for_instance(self):
        budget = UserBudgetService.get_budget_for_instance(self.user)
        self.assertIsNotNone(budget)
        self.assertEqual(budget.id, self.budget.id)

    def test_delete_user_budget(self):
        UserBudgetService.delete_user_budget(self.user)
        self.assertFalse(Budget.objects.filter(id=self.budget.id).exists())
