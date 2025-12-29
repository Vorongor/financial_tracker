from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Q, Case, When, F, IntegerField

from accounts.models import UserConnection
from dashboard.services.event_stats import EventAnalyticsService
from finances.forms import TransferCreateForm
from finances.models import Category
from events.models import EventMembership, Event


User = get_user_model()

class EventDetailContextService:
    """
    Builds full context for EventDetailView.
    Encapsulates membership logic, permissions, budget,
    transaction history, categories, forms, analytics, and invites.
    """

    @classmethod
    def build_context(cls, *, event: Event, user: User) -> dict[str, Any]:
        context = {}

        budget = event.budget

        members_qs = EventMembership.objects.filter(
            event=event
        ).select_related("user")

        user_membership = next(
            (m for m in members_qs if m.user_id == user.id),
            None
        )
        user_role = getattr(user_membership, "role", None)

        can_delete_event = (
                (event.creator_id == user.id)
                or (not event.creator and user_role == "Admin")
        )

        member_ids = members_qs.values_list("user_id", flat=True)

        accepted_connections = UserConnection.objects.filter(
            status=UserConnection.Status.ACCEPTED
        ).filter(
            Q(from_user=user) | Q(to_user=user)
        )

        connected_user_ids = accepted_connections.annotate(
            other_id=Case(
                When(from_user=user, then=F("to_user_id")),
                default=F("from_user_id"),
                output_field=IntegerField(),
            )
        ).values_list("other_id", flat=True)

        potential_invites = get_user_model().objects.filter(
            id__in=connected_user_ids
        ).exclude(
            id__in=member_ids
        )

        try:
            context["current_budget"] = budget.get_budget_data()
            context[
                "transaction_history"] = budget.transactions.select_related(
                "category", "payer"
            ).all()
        except AttributeError:
            context["current_budget"] = None
            context["transaction_history"] = []

        categories = Category.objects.all()

        if event.event_type == event.EventType.ACCUMULATIVE:
            categories = categories.filter(category_type=Category.Types.INCOME)

        if event.event_type == event.EventType.EXPENSES:
            categories = categories.filter(
                category_type=Category.Types.EXPENSE)

        form = TransferCreateForm()
        all_choices = form.fields["transaction_type"].choices

        if event.event_type == event.EventType.EXPENSES:
            form.fields["transaction_type"].choices = [
                c for c in all_choices if c[0] == "EXPENSE"
            ]
        elif event.event_type == event.EventType.ACCUMULATIVE:
            form.fields["transaction_type"].choices = [
                c for c in all_choices if c[0] == "INCOME"
            ]

        if event.event_type == Event.EventType.SAVINGS:
            context["savings_chart_data_json"] = (
                EventAnalyticsService.get_event_savings_stats(budget=budget)
            )

        elif event.event_type == Event.EventType.EXPENSES:
            context["expenses_chart_data"] = (
                EventAnalyticsService.get_event_expense_stats(
                    start=event.start_date,
                    end=event.end_date,
                    budget=budget,
                    total_expense=event.planned_amount,
                )
            )

        elif event.event_type == Event.EventType.ACCUMULATIVE:
            context["accum_chart_data"] = (
                EventAnalyticsService.accumulate_stats(
                    start=event.start_date,
                    end=event.end_date,
                    budget=budget,
                    planed_goal=event.planned_amount,
                )
            )

        context[
            "analytics"
        ] = EventAnalyticsService.get_event_accumulative_stats(
            event,
            budget
        )

        context["social_analytics"] = EventAnalyticsService.get_social_stats(
            event, budget
        )

        if event.accessibility == Event.Accessibility.PRIVATE:
            connects = []
            members = []
        else:
            connects = potential_invites
            members = members_qs

        context.update(
            {
                "categories": categories,
                "can_delete_event": can_delete_event,
                "transaction_form": form,
                "content_type": "event",
                "object_id": event.id,
                "user_role": user_role,
                "connects": connects,
                "members": members,
            }
        )

        return context
