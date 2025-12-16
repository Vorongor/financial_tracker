from django.db import models


# class Status(models.TextChoices):
#     ACTIVE = "AC", "Active"
#     BANNED = "BN", "Banned"
#     DISABLED = "DI", "Disabled"


class Status(models.TextChoices):
    PENDING = "Pending",
    ACCEPTED = "Accepted",
    BANNED = "Banned"

class Role(models.TextChoices):
    ADMIN = "Admin"
    MODERATOR =  "Moderator"
    MEMBER = "Member"