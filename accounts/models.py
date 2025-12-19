import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.db import models

from config import settings
from finances.models import Budget


class User(AbstractUser):
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    job = models.CharField(max_length=255, blank=True)
    salary = models.PositiveIntegerField(default=0)
    default_currency = models.CharField(max_length=255, default="UAH")
    connect_key = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["username", "email"],
                name="unique_email_for_each_user",
            ),
        ]

    def __str__(self):
        return self.first_name + " " + self.last_name

    @property
    def budget(self):
        """
        Return the Budget instance for this User, or None.
        Expects at most one Budget due to unique constraint in Budget.meta.
        """
        ct = ContentType.objects.get_for_model(self)
        return Budget.objects.filter(
            content_type=ct,
            object_id=self.id
        ).first()

    def get_user_uniq_key(self):
        return str(self.connect_key)


class UserConnection(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending"
        ACCEPTED = "Accepted"
        BLOCKED = "Blocked"

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_connections",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_connections",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_user", "to_user"], name="unique_connection"
            )
        ]

    def other_user(self, user):
        """
        back other user's connections
        """
        if self.from_user_id == user.id:
            return self.to_user
        if self.to_user_id == user.id:
            return self.from_user
        raise ValueError("User is not part of this connection")
