from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from events.models import Event
from finances.models import Transaction
from groups.models import Group


class TransactionHistoryService:
    @classmethod
    def get_user_transactions(cls, user_id: int) -> QuerySet:
        User = get_user_model()
        user = get_object_or_404(User, pk=user_id)

        return Transaction.objects.filter(payer=user)

    @classmethod
    def get_event_transactions(cls, event_id: int) -> QuerySet:
        event = get_object_or_404(Event, id=event_id)

        return Transaction.objects.filter(target=event.budget)

    @classmethod
    def get_group_transactions(cls, group_id: int) -> QuerySet:
        group = get_object_or_404(Group, pk=group_id)

        return Transaction.objects.filter(target=group.budget)
