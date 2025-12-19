from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from events.models import Event
from finances.models import Transaction
from groups.models import Group


def get_user_transactions(self, user_id):
    if user_id != self.request.user.id:
        raise ValueError("User is not valid")

    return Transaction.objects.filter(payer=self.request.user)


def get_event_transactions(self, event_id):
    event = get_object_or_404(Event, id=event_id)

    return Transaction.objects.filter(target=event.budget)


def get_group_transactions(self, group_id):
    group = get_object_or_404(Group, pk=group_id)

    return Transaction.objects.filter(target=group.budget)
