from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import UserConnection

User = get_user_model()


class AccountsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = (
            User.objects.create_user(
                username="testuser",
                password="password123"
            )
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="password123"
        )
        self.client.login(
            username="testuser",
            password="password123"
        )

    def test_profile_view_requires_login(self):
        self.client.logout()
        response = self.client.get(
            reverse(
                "profile-page",
                kwargs={"pk": self.user.pk}
            ))
        self.assertEqual(response.status_code, 302)

    def test_profile_context_data(self):
        response = self.client.get(
            reverse(
                "profile-page",
                kwargs={"pk": self.user.pk}
            ))
        self.assertEqual(response.status_code, 200)
        self.assertIn("connections", response.context)
        self.assertIn("invite_to_connect", response.context)

    def test_community_list_excludes_friends(self):
        UserConnection.objects.create(
            from_user=self.user,
            to_user=self.other_user,
            status="Accepted"
        )
        response = self.client.get(reverse("community-list"))
        users_in_list = response.context["user_connections"]
        self.assertNotIn(self.other_user, users_in_list)


class ConnectionActionsTest(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            username="user_a",
            password="password123"
        )
        self.user_b = User.objects.create_user(
            username="user_b",
            password="password123"
        )
        self.client.login(
            username="user_a",
            password="password123"
        )

    def test_user_connect_view_post(self):
        url = reverse(
            "user-connect",
            kwargs={"user_id": self.user_b.id}
        )
        response = self.client.post(
            url,
            HTTP_REFERER=reverse("community-list")
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(UserConnection.objects.filter(
            from_user=self.user_a,
            to_user=self.user_b
        ).exists())

    def test_approve_connection_view(self):
        conn = UserConnection.objects.create(
            from_user=self.user_b,
            to_user=self.user_a,
            status="Pending"
        )
        url = reverse(
            "approve-connect",
            kwargs={"connection_id": conn.id}
        )
        self.client.post(url)

        conn.refresh_from_db()
        self.assertEqual(
            conn.status,
            UserConnection.Status.ACCEPTED
        )

    def test_connect_by_unique_key_success(self):
        url = reverse(
            "user-invite-uk",
            kwargs={
                "invite_type": "connection",
                "sender_id": self.user_a.id
            }
        )
        data = {"unik_key": str(self.user_b.connect_key)}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(UserConnection.objects.filter(
            from_user=self.user_a,
            to_user=self.user_b
        ).exists())


class DeleteProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="delete_me",
            password="password123"
        )
        self.client.login(
            username="delete_me",
            password="password123"
        )

    def test_delete_profile_cleans_up(self):
        url = reverse("profile-delete", kwargs={"pk": self.user.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
