from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    job = models.CharField(max_length=255, blank=True)
    salary = models.PositiveIntegerField(default=0)
    default_currency = models.CharField(max_length=255, default='UAH')

    class Meta:
        db_table = "user"
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