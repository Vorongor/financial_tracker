import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property

from accounts.services.user_budget_service import UserBudgetService
from finances.models import Budget


class Currency(models.TextChoices):
    USD = "USD"
    EUR = "EUR"
    JPY = "JPY"
    CHF = "CHF"
    DKK = "DKK"
    UAH = "UAH"
    GBP = "GBP"
    AUD = "AUD"
    CAD = "CAD"
    CNY = "CNY"
    HKD = "HKD"
    NZD = "NZD"
    SEK = "SEK"
    NOK = "NOK"
    INR = "INR"
    SGD = "SGD"


class User(AbstractUser):
    job = models.CharField(max_length=255, blank=True, default="")
    salary = models.PositiveIntegerField(default=0)
    default_currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD,
    )
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

    def __str__(self):
        return self.first_name + " " + self.last_name

    @cached_property
    def budget(self) -> Budget:
        return UserBudgetService.get_budget_for_instance(self)

    def get_user_uniq_key(self) -> str:
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
        ordering = ["status"]
        constraints = [
            models.UniqueConstraint(
                fields=["from_user", "to_user"], name="unique_connection"
            )
        ]

    def clean(self) -> None:
        if self.from_user_id == self.to_user_id:
            raise ValidationError("User cannot connect to himself.")

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def other_user(self, user: User) -> User:
        """
        back other user's connections
        """
        if self.from_user_id == user.id:
            return self.to_user
        if self.to_user_id == user.id:
            return self.from_user
        raise ValueError("User is not part of this connection")
