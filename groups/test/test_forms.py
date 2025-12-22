from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from events.models import Event
from groups.forms import GroupCreateForm, GroupEventCreateForm
from groups.models import Group
from datetime import date, timedelta

User = get_user_model()


class GroupFormsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="1Qazcde3"
        )

    @patch(
        "accounts.services.receive_connection"
        ".UserConnectionsService.get_user_connections")
    def test_group_create_form_participants_initialization(
            self,
            mock_connections
    ):
        mock_friend = MagicMock()
        mock_friend.id = 99
        mock_friend.username = "friend_user"
        mock_conn = MagicMock()
        mock_conn.other_user.return_value = mock_friend
        mock_connections.return_value = [mock_conn]
        form = GroupCreateForm(user=self.user)
        choices = form.fields["participants"].choices
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0], (99, "friend_user"))

    def test_group_create_form_permanent_invalid_dates(self):
        form_data = {
            "name": "Permanent Group",
            "state": Group.States.PERMANENT,
            "start_date": date.today(),
        }
        form = GroupCreateForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_event_create_form_date_validation(self):
        form_data = {
            "name": "Future Event",
            "start_date": date.today() + timedelta(days=5),
            "end_date": date.today(),
            "planned_amount": 100.00,
            "event_type": "Conference",
            "status": "Planned"
        }
        form = GroupEventCreateForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("End date cannot be earlier than start date.",
                      form.non_field_errors())

    def test_event_create_form_negative_amount(self):
        form_data = {
            "name": "Bad Amount Event",
            "planned_amount": -100.00,
        }
        form = GroupEventCreateForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("planned_amount", form.errors)

    def test_event_create_form_valid(self):
        form_data = {
            "name": "Good Event",
            "start_date": date.today(),
            "end_date": date.today() + timedelta(days=1),
            "planned_amount": 500.00,
            "event_type": Event.EventType.SAVINGS,
            "status": Event.EventStatus.PLANNED
        }
        form = GroupEventCreateForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
