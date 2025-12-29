from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from dashboard.services.event_stats import EventAnalyticsService
from finances.models import Transaction, Budget
from events.models import Event, EventMembership


class EventAnalyticsServiceTest(TestCase):

    def setUp(self):
        self.user1 = get_user_model().objects.create_user(
            username="user1",
            password="pass"
        )
        self.user2 = get_user_model().objects.create_user(
            username="user2",
            password="pass"
        )

        self.event = Event.objects.create(
            name="Test Event",
            end_date=timezone.now().date(),
        )

        self.budget = self.event.budget

        self.budget.current_amount = Decimal("800")
        self.budget.planned_amount = Decimal("1000")
        self.budget.save()

    def create_transaction(self, *, amount, days_ago=0, payer):
        return Transaction.objects.create(
            target=self.budget,
            transaction_type="Income",
            amount=Decimal(amount),
            payer=payer,
            date=timezone.now() - timedelta(days=days_ago),
        )

    def test_event_stats_percent_and_color(self):
        result = EventAnalyticsService.get_event_accumulative_stats(
            self.event, self.budget
        )

        self.assertEqual(result["percent"], 80.0)
        self.assertEqual(result["gauge_color"], "#ffc107")

    def test_event_stats_percent_capped_at_100(self):
        self.budget.current_amount = Decimal("2000")
        self.budget.save()

        result = EventAnalyticsService.get_event_accumulative_stats(
            self.event, self.budget
        )

        self.assertEqual(result["percent"], 100)

    def test_event_stats_labels_and_points_length(self):
        result = EventAnalyticsService.get_event_accumulative_stats(
            self.event, self.budget
        )

        self.assertEqual(len(result["labels"]), 31)
        self.assertEqual(len(result["data_points"]), 31)

    def test_event_stats_daily_aggregation(self):
        self.create_transaction(amount="100", days_ago=5, payer=self.user1)
        self.create_transaction(amount="200", days_ago=5, payer=self.user2)
        self.create_transaction(amount="50", days_ago=1, payer=self.user1)

        result = EventAnalyticsService.get_event_accumulative_stats(
            self.event, self.budget
        )

        # беремо позицію дня "5 днів тому"
        index = 30 - 5
        self.assertEqual(result["data_points"][index], 300.0)

    def test_social_stats_leaderboard(self):
        self.create_transaction(amount="300", payer=self.user1)
        self.create_transaction(amount="100", payer=self.user2)

        data = EventAnalyticsService.get_social_stats(
            self.event, self.budget
        )

        self.assertEqual(len(data["leaderboard"]), 2)
        self.assertEqual(
            data["leaderboard"][0]["payer__username"], "user1"
        )
        self.assertEqual(
            float(data["leaderboard"][0]["total_contributed"]), 300.0
        )

    def test_social_stats_status_counts(self):
        EventMembership.objects.create(
            event=self.event,
            user=self.user1,
            role="Owner",
        )
        EventMembership.objects.create(
            event=self.event,
            user=self.user2,
            role="Member",
        )

        data = EventAnalyticsService.get_social_stats(
            self.event, self.budget
        )

        self.assertIn("Owner", data["status_labels"])
        self.assertIn("Member", data["status_labels"])
        self.assertIn(1, data["status_data"])
