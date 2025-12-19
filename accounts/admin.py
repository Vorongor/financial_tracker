from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + (
        "job",
        "salary",
        "default_currency",
        "is_superuser",
        "is_active",
    )
    fieldsets = UserAdmin.fieldsets + (
        ("Additional info", {"fields": ("job", "salary", "default_currency")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Additional info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "job",
                    "salary",
                    "default_currency",
                )
            },
        ),
    )
