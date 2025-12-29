from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.forms import UserRegisterForm, UserUpdateForm

User = get_user_model()


class UserRegisterFormTest(TestCase):
    def setUp(self):
        self.existing_user = User.objects.create_user(
            username="existing_bob",
            email="bob@test.com"
        )

    def test_username_uniqueness_validation(self):
        data = {
            "username": "existing_bob",
            "email": "new@test.com",
            "first_name": "New",
            "last_name": "User",
            "password1": "password123",
            "password2": "password123",
        }
        form = UserRegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "This username is already taken.",
            form.errors["username"])


class UserUpdateFormTest(TestCase):
    def test_fields_present_in_update_form(self):
        form = UserUpdateForm()
        fields = list(form.fields.keys())
        self.assertEqual(fields, [
            "username", "email", "first_name", "last_name",
            "job", "salary", "default_currency"
        ])
