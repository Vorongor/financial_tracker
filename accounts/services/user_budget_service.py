from django.contrib.contenttypes.models import ContentType

from finances.models import Budget


class UserBudgetService:
    @classmethod
    def get_budget_for_instance(cls, instance) -> Budget:
        ct = ContentType.objects.get_for_model(instance)
        return Budget.objects.filter(
            content_type=ct,
            object_id=instance.id
        ).first()

    @classmethod
    def delete_user_budget(cls, user) -> None:
        ct = ContentType.objects.get_for_model(user)
        Budget.objects.get(content_type=ct, object_id=user.id).delete()
