from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from config import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.contrib.contenttypes.models import ContentType

from django.contrib.contenttypes.fields import GenericForeignKey


class Budget(models.Model):
    """
    Universal budget that can belong to any model via GenericForeignKey.
    Enforce uniqueness on (content_type, object_id) so one budget per owner.
    """

    # GFK
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    owner = GenericForeignKey("content_type", "object_id")

    total_income = models.DecimalField(max_digits=12, decimal_places=2,
                                       default=0)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2,
                                         default=0)
    current_amount = models.DecimalField(default=0, max_digits=10,
                                         decimal_places=2)
    start_amount = models.DecimalField(max_digits=12, decimal_places=2,
                                       default=0)
    planned_amount = models.DecimalField(max_digits=12, decimal_places=2,
                                         default=0)

    timestamp_create = models.DateTimeField(auto_now_add=True)
    timestamp_update = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "budgets"
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id"],
                name="unique_budget_per_owner"
            )
        ]
        ordering = ("-timestamp_update",)

    def __str__(self):
        return f"Budget of {self.owner} ({self.current_amount})"

    def get_owner(self) -> str:
        return self.owner

    def get_budget_data(self):
        return {
            "total_income": self.total_income,
            "total_expenses": self.total_expenses,
            "current_amount": self.current_amount,
            "start_amount": self.start_amount,
            "planned_amount": self.planned_amount,
        }

    def clean(self):
        for field in (
                "total_income",
                "total_expenses",
                "start_amount",
                "planned_amount",
        ):
            validator = getattr(self, field)
            if validator is None or validator < 0:
                raise ValidationError({field: "Must be non-negative."})

    @transaction.atomic
    def recalc(self, save: bool = True):
        incomes = self.transactions.filter(
            transaction_type=Transaction.Types.INCOME
        ).aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0.00")

        expenses = self.transactions.filter(
            transaction_type=Transaction.Types.EXPENSE
        ).aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0.00")
        amount = self.start_amount or Decimal("0.00")
        current_amount = amount + incomes - expenses
        self.total_income = incomes
        self.total_expenses = expenses
        self.current_amount = current_amount

        if save:
            self.full_clean()
            self.save(
                update_fields=[
                    "total_income",
                    "total_expenses",
                    "current_amount",
                    "timestamp_update",
                ]
            )


class Category(models.Model):
    class Types(models.TextChoices):
        INCOME = "Income"
        EXPENSE = "Expense"

    name = models.CharField(max_length=120, unique=True)
    category_type = models.CharField(max_length=20, choices=Types.choices)
    color_hex = models.CharField(max_length=7, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order_index = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "categories"
        verbose_name_plural = "Categories"
        ordering = ("order_index", "name")

    def __str__(self):
        return self.name


class Transaction(models.Model):
    class Types(models.TextChoices):
        INCOME = "Income"
        EXPENSE = "Expense"

    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=Types.choices,
        default=Types.INCOME,
    )
    date = models.DateTimeField(default=timezone.now)
    timestamp_create = models.DateTimeField(auto_now_add=True)
    target = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    note = models.TextField(blank=True)

    class Meta:
        db_table = "transactions"
        ordering = ("-date", "-timestamp_create")

    def __str__(self):
        return (f"{self.get_transaction_type_display()} {self.amount} "
                f"-> {self.target}")

    def get_short_description(self):
        return (f"{self.amount} -> {self.transaction_type}, "
                f"from {self.payer.username}")

    def get_full_description(self):
        return (f"{self.amount} -> {self.transaction_type}, "
                f"from {self.payer.username} "
                f"to {self.target.get_owner()} "
                f"at {self.date}")

    def clean(self):
        if self.category and self.transaction_type:
            if (
                    self.category.category_type == Category.Types.INCOME
                    and self.transaction_type != self.Types.INCOME
            ):
                raise ValidationError(
                    {
                        "category": "Category type conflicts "
                                    "with transaction type.(INCOME)"}
                )
            if (
                    self.category.category_type == Category.Types.EXPENSE
                    and self.transaction_type != self.Types.EXPENSE
            ):
                raise ValidationError(
                    {
                        "category": "Category type conflicts "
                                    "with transaction type. (EXPENSE)"}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
