
from django.contrib.contenttypes.models import ContentType

from finances.models import Budget


def get_budget_for_instance(instance):
    ct = ContentType.objects.get_for_model(instance)
    return Budget.objects.filter(
        content_type=ct,
        object_id=instance.id
    ).first()
