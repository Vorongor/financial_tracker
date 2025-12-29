from django.test import TestCase
from unittest.mock import MagicMock, patch

from events.forms import EventPrivateCreateForm
from events.models import Event


class TestEventPrivateCreateForm(TestCase):
    def setUp(self):
        self.user = MagicMock()
        self.user.id = 1

    @patch("events.forms.UserConnectionsService.get_user_connections")
    def test_init_participants_choices(self, mock_get_connections):
        mock_connection = MagicMock()
        other_user = MagicMock()
        other_user.id = 99
        other_user.username = "friend_user"
        mock_connection.other_user.return_value = other_user

        mock_get_connections.return_value = [mock_connection]

        form = EventPrivateCreateForm(user=self.user)

        expected_choices = [(99, "friend_user")]
        self.assertEqual(form.fields["participants"].choices, expected_choices)

    @patch("events.forms.UserConnectionsService.get_user_connections",
           return_value=[])
    def test_clean_dates_invalid(self, _):
        data = {
            "name": "Test Event",
            "description": "",
            "start_date": "2023-10-10",
            "end_date": "2023-10-01",
            "planned_amount": 100,
            "event_type": Event.EventType.EXPENSES,
            "accessibility": Event.Accessibility.PRIVATE,
            "status": Event.EventStatus.PLANNED,
        }

        form = EventPrivateCreateForm(data=data, user=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "End date cannot be earlier than start date.",
            form.non_field_errors()
        )

    @patch("events.forms.UserConnectionsService.get_user_connections",
           return_value=[])
    def test_clean_planned_amount_negative(self, _):
        data = {
            "name": "Test Event",
            "description": "",
            "start_date": "2023-10-01",
            "end_date": "2023-10-10",
            "planned_amount": -10.50,
            "event_type": Event.EventType.EXPENSES,
            "accessibility": Event.Accessibility.PRIVATE,
            "status": Event.EventStatus.PLANNED,
        }

        form = EventPrivateCreateForm(data=data, user=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Planned amount must be greate than zero",
            form.non_field_errors()
        )

    @patch("events.forms.UserConnectionsService.get_user_connections",
           return_value=[])
    def test_clean_valid_data(self, _):
        data = {
            "name": "Valid Event",
            "description": "",
            "start_date": "2023-10-01",
            "end_date": "2023-10-10",
            "planned_amount": 500,
            "event_type": Event.EventType.EXPENSES,
            "accessibility": Event.Accessibility.PRIVATE,
            "status": Event.EventStatus.PLANNED,
        }

        form = EventPrivateCreateForm(data=data, user=self.user)

        self.assertTrue(form.is_valid())
