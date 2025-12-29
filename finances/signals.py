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
def create_budget_for_user(
        sender,
        instance: User,
        created: bool,
        **kwargs
) -> None:
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
def create_budget_for_group(
        sender,
        instance: Group,
        created: bool,
        **kwargs
) -> None:
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
def create_budget_for_event(
        sender,
        instance: Event,
        created: bool,
        **kwargs) -> None:
    if created:
        ct = ContentType.objects.get_for_model(instance)

        Budget.objects.get_or_create(
            content_type=ct,
            object_id=instance.id,
            defaults={
                "planned_amount": instance.planned_amount,
            },
        )


@receiver([post_save, post_delete], sender=Transaction)
def update_budget_on_change(sender, instance: Transaction, **kwargs) -> None:
    if instance.target:
        instance.target.recalc()