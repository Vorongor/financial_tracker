from decimal import Decimal

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from events.models import Event
from groups.models import Group
from .models import Budget, Transaction

User = get_user_model()


@receiver(post_save, sender=User)
def create_budget_for_user(sender, instance, created, **kwargs):
    if created:
        ct = ContentType.objects.get_for_model(instance)

        Budget.objects.get_or_create(
            content_type=ct,
            object_id=instance.id,
            defaults={
                "planned_amount": Decimal("0.00"),
            },
        )


@receiver(post_save, sender=Group)
def create_budget_for_group(sender, instance, created, **kwargs):
    if created:
        ct = ContentType.objects.get_for_model(instance)

        Budget.objects.get_or_create(
            content_type=ct,
            object_id=instance.id,
            defaults={
                "planned_amount": Decimal("0.00"),
            },
        )


@receiver(post_save, sender=Event)
def create_budget_for_event(sender, instance, created, **kwargs):
    if created:
        ct = ContentType.objects.get_for_model(instance)

        Budget.objects.get_or_create(
            content_type=ct,
            object_id=instance.id,
            defaults={
                "planned_amount": instance.planned_amount,
            },
        )
