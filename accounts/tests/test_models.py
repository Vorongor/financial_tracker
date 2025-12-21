from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from accounts.models import UserConnection

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            first_name="Ivan",
            last_name="Ivanov",
            job="Developer",
            salary=1000
        )

    def test_user_str_method(self):
        self.assertEqual(str(self.user), "Ivan Ivanov")

    def test_get_user_uniq_key(self):
        key = self.user.get_user_uniq_key()
        self.assertIsInstance(key, str)
        self.assertEqual(key, str(self.user.connect_key))

    def test_connect_key_uniqueness(self):
        user2 = User.objects.create_user(username="user2")
        self.assertNotEqual(self.user.connect_key, user2.connect_key)


class UserConnectionModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1")
        self.user2 = User.objects.create_user(username="user2")
        self.user3 = User.objects.create_user(username="user3")

    def test_cannot_connect_to_self(self):
        connection = UserConnection(from_user=self.user1, to_user=self.user1)
        with self.assertRaises(ValidationError) as cm:
            connection.save()
        self.assertIn("User cannot connect to himself.", str(cm.exception))

    def test_other_user_method(self):
        connection = UserConnection.objects.create(
            from_user=self.user1,
            to_user=self.user2
        )
        self.assertEqual(connection.other_user(self.user1), self.user2)
        self.assertEqual(connection.other_user(self.user2), self.user1)

    def test_other_user_raises_error_if_not_member(self):
        connection = UserConnection.objects.create(
            from_user=self.user1,
            to_user=self.user2
        )
        with self.assertRaises(ValueError):
            connection.other_user(self.user3)
