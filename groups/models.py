from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from addition_info.choise_models import Role, Status
from config import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from events.models import Event
from finances.models import Budget


class Group(models.Model):
    class States(models.TextChoices):
        PERMANENT = "Permanent"
        TEMPORARY = "Temporary"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    state = models.CharField(
        max_length=20,
        choices=States.choices,
        default=States.PERMANENT,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="group_creator",
    )
    timestamp_created = models.DateTimeField(auto_now_add=True)
    timestamp_updated = models.DateTimeField(auto_now=True)
    budgets = GenericRelation(Budget)

    class Meta:
        db_table = "a_groups"

    def __str__(self):
        return f"{self.name} ({self.state})"

    def clean(self):
        if self.state == self.States.PERMANENT:
            if self.start_date or self.end_date:
                raise ValidationError("Permanent groups must not have start/end dates.")
        else:
            if self.start_date and self.end_date and self.end_date < self.start_date:
                raise ValidationError("end_date must be >= start_date.")

    @property
    def budget(self):
        """
        Return the Budget instance for this User, or None.
        Expects at most one Budget due to unique constraint in Budget.meta.
        """
        ct = ContentType.objects.get_for_model(self)
        return Budget.objects.filter(content_type=ct, object_id=self.id).first()


class GroupMembership(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="groupslink",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="groupslink",
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
        db_table = "group_membership"
        constraints = [
            models.UniqueConstraint(
                fields=["group", "user"],
                name="unique_group_user",
            )
        ]


class GroupEventConnection(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="event_link",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="group_link",
    )
    join_date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "group_event_connections"
        constraints = [
            models.UniqueConstraint(
                fields=["group", "event"],
                name="unique_group_event",
            )
        ]

    def get_related_events(self):
        return (
            f"{self.event.name} ({self.event.type} "
            f"- {self.event.status}) - {self.join_date}"
        )
