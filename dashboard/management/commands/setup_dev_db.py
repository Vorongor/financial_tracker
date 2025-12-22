from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Runs all database populating scripts in the correct order"

    def handle(self, *args, **kwargs):

        commands = [
            ("seed_users", "Users"),
            ("seed_events", "Events"),
            ("seed_groups", "Groups"),
            ("seed_categories", "Categories"),
            ("seed_connections", "Users Connections"),
            ("seed_transactions", "Transactions"),
        ]

        self.stdout.write(self.style.MIGRATE_HEADING("--- Starting full database initialization ---"))

        for command_name, description in commands:
            self.stdout.write(f"Run: {description} ({command_name})...")
            try:
                call_command(command_name)
                self.stdout.write(self.style.SUCCESS(f"Successfully completed: {description}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in {command_name}: {e}"))
                return

        self.stdout.write(self.style.MIGRATE_LABEL("\n--- The database is ready to go! ---"))