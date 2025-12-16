from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

from addition_info.choise_models import Role, Status
from config import settings

from finances.models import Budget


class Event(models.Model):
    class EventType(models.TextChoices):
        SAVINGS = 'Savings'
        EXPENSES = 'Expenses'
        ACCUMULATIVE = 'Accumulative'

    class EventStatus(models.TextChoices):
        PLANNED = 'Planned'
        COMPLETED = 'Completed'
        ONGOING = 'Ongoing'
        CANCELLED = 'Cancelled'

    class Accessibility(models.TextChoices):
        PRIVATE = 'Private'
        PUBLIC = 'Public'
        GROUP = 'Group'

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    planned_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.SAVINGS,
    )
    status = models.CharField(
        max_length=20,
        choices=EventStatus.choices,
        default=EventStatus.PLANNED
    )
    accessibility = models.CharField(
        max_length=20,
        choices=Accessibility.choices,
        default=Accessibility.PRIVATE,
    )
    timestamp_create = models.DateTimeField(auto_now_add=True)
    timestamp_update = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    budgets = GenericRelation(
        Budget,
        related_query_name="event_budget"
    )

    class Meta:
        db_table = "events_table"

    def __str__(self):
        return f"Event: {self.name} - {self.status}"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError(
                {"end_date": "end_date must be >= start_date."})
        if self.planned_amount < 0:
            raise ValidationError(
                {"planned_budget": "planned_budget must be non-negative."})

    @property
    def budget(self):
        """
        Return the Budget instance for this User, or None.
        Expects at most one Budget due to unique constraint in Budget.meta.
        """
        ct = ContentType.objects.get_for_model(self)
        return Budget.objects.filter(content_type=ct, object_id=self.id).first()


class EventMembership(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    join_date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "events_membership"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"],
                name="unique_event_user"
            )
        ]
