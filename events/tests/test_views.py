from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from events.models import Event, EventMembership
from addition_info.choise_models import Status, Role

User = get_user_model()


class EventViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="1Qazcde3",
            email="test1@gmail.com"
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            password="2Wsxvfr4",
            email="test2@gmail.com"
        )
        self.client.login(username="testuser", password="1Qazcde3")

        self.event = Event.objects.create(
            name="Test Event",
            creator=self.user,
            accessibility=Event.Accessibility.PUBLIC
        )

    def test_event_hero_view_context(self):
        response = self.client.get(reverse("events:event-hero"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/events_list.html")
        self.assertIn("private_events", response.context)

    @patch("events.views.EventDetailContextService.build_context")
    def test_event_detail_view(self, mock_build_context):
        # Provide the keys your template expects
        mock_build_context.return_value = {
            "invite_type": "event",
            "sender_id": 1,
            "categories": [],
            "can_delete_event": False,
            "transaction_form": None,
            "content_type": "event",
            "object_id": 1,
            "user_role": None,
            "connects": [],
            "members": [],
        }

        EventMembership.objects.create(
            event=self.event,
            user=self.user,
            role=Role.CREATOR
        )

        response = self.client.get(
            reverse("events:event-detail", kwargs={"pk": self.event.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["object"].id, self.event.id)

        mock_build_context.assert_called_once_with(
            event=self.event,
            user=self.user
        )

    @patch("events.views.EventInvitationService.create_event_invitation")
    @patch("events.views.UserConnectionsService.get_user_connections")
    def test_event_create_post(
            self,
            mock_get_connections,
            mock_create_invitation
    ):
        class FakeConnection:
            def __init__(self, other):
                self._other = other

            def other_user(self, user):
                return self._other

        mock_get_connections.return_value = [
            FakeConnection(self.other_user)
        ]

        data = {
            "name": "New Private Event",
            "description": "Some description",
            "start_date": "2025-12-01",
            "end_date": "2025-12-02",
            "planned_amount": "100.00",
            "event_type": Event.EventType.ACCUMULATIVE,
            "accessibility": Event.Accessibility.PUBLIC,
            "status": Event.EventStatus.PLANNED,
            "participants": [str(self.other_user.id)],
        }

        response = self.client.post(
            reverse("events:private-event-create"),
            data
        )

        self.assertEqual(response.status_code, 302)

        event = Event.objects.get(name="New Private Event")

        self.assertEqual(event.creator, self.user)
        self.assertEqual(event.accessibility, Event.Accessibility.PUBLIC)

        self.assertTrue(
            event.memberships.filter(
                user=self.user,
                role=Role.CREATOR,
                status=Status.ACCEPTED
            ).exists()
        )

        mock_create_invitation.assert_called_once_with(
            list_of_connects=[self.other_user.id],
            event_id=event.id
        )

    @patch("events.views.EventInvitationService.accept_event_invitation")
    def test_event_accept_invite_view(self, mock_accept):
        url = reverse(
            "events:event-accept-members",
            kwargs={"pk": self.event.pk}
        )
        response = self.client.post(url)

        mock_accept.assert_called_once_with(
            event_id=self.event.pk,
            user_id=self.user.id
        )
        self.assertRedirects(response, reverse(
            "events:event-detail",
            kwargs={"pk": self.event.pk}
        ))

    @patch("events.views.EventInvitationService.leave_event")
    def test_event_leave_view(self, mock_leave):
        url = reverse(
            "events:event-leave",
            kwargs={"pk": self.event.pk}
        )
        response = self.client.post(url)

        mock_leave.assert_called_once()
        self.assertRedirects(response, reverse("events:event-hero"))

    def test_event_update_post_success(self):
        data = {
            "name": "Updated Name",
            "description": "New Desc",
            "start_date": "2025-01-01",
            "end_date": "2025-01-02",
            "status": Event.EventStatus.PLANNED,
            "event_type": Event.EventType.ACCUMULATIVE,
            "planned_amount": 500,
            "start_amount": 0,
        }

        url = reverse(
            "events:event-update",
            kwargs={"pk": self.event.pk}
        )

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)

        self.event.refresh_from_db()
        self.event.budget.refresh_from_db()

        self.assertEqual(self.event.name, "Updated Name")
        self.assertEqual(self.event.budget.planned_amount, 500)
        self.assertEqual(self.event.planned_amount, 500)

        self.assertRedirects(
            response,
            reverse("events:event-detail", kwargs={"pk": self.event.pk})
        )
