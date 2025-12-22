from django.core.management.base import BaseCommand
from finances.models import Category


class Command(BaseCommand):
    help_tag = "Loads initial financial categories from a predefined list"

    def handle(self, *args, **options):
        categories_data = [
            {"name": "Salary", "type": "Income", "color_hex": "#2ECC71",
             "order_index": 1},
            {"name": "Freelance", "type": "Income", "color_hex": "#3498DB",
             "order_index": 2},
            {"name": "Investments", "type": "Income", "color_hex": "#9B59B6",
             "order_index": 3},
            {"name": "Business", "type": "Income", "color_hex": "#34495E",
             "order_index": 4},
            {"name": "Gifts", "type": "Income", "color_hex": "#F1C40F",
             "order_index": 5},
            {"name": "Rental Income", "type": "Income", "color_hex": "#E67E22",
             "order_index": 6},
            {"name": "Refunds", "type": "Income", "color_hex": "#1ABC9C",
             "order_index": 7},
            {"name": "Other Income", "type": "Income", "color_hex": "#7F8C8D",
             "order_index": 8},
            {"name": "Groceries", "type": "Expense", "color_hex": "#E74C3C",
             "order_index": 10},
            {"name": "Dining Out", "type": "Expense", "color_hex": "#D35400",
             "order_index": 11},
            {"name": "Housing / Rent", "type": "Expense",
             "color_hex": "#C0392B", "order_index": 12},
            {"name": "Utilities", "type": "Expense", "color_hex": "#F39C12",
             "order_index": 13},
            {"name": "Transportation", "type": "Expense",
             "color_hex": "#2980B9", "order_index": 14},
            {"name": "Vehicle Maintenance", "type": "Expense",
             "color_hex": "#2C3E50", "order_index": 15},
            {"name": "Health & Medical", "type": "Expense",
             "color_hex": "#16A085", "order_index": 16},
            {"name": "Entertainment", "type": "Expense",
             "color_hex": "#8E44AD", "order_index": 17},
            {"name": "Shopping", "type": "Expense", "color_hex": "#27AE60",
             "order_index": 18},
            {"name": "Clothing", "type": "Expense", "color_hex": "#E84393",
             "order_index": 19},
            {"name": "Education", "type": "Expense", "color_hex": "#0984E3",
             "order_index": 20},
            {"name": "Personal Care", "type": "Expense",
             "color_hex": "#FD79A8", "order_index": 21},
            {"name": "Sports & Fitness", "type": "Expense",
             "color_hex": "#00CEC9", "order_index": 22},
            {"name": "Travel", "type": "Expense", "color_hex": "#00B894",
             "order_index": 23},
            {"name": "Debt Payments", "type": "Expense",
             "color_hex": "#636E72", "order_index": 24},
            {"name": "Charity", "type": "Expense", "color_hex": "#55E6C1",
             "order_index": 25},
            {"name": "Pets", "type": "Expense", "color_hex": "#A29BFE",
             "order_index": 26},
            {"name": "Subscriptions", "type": "Expense",
             "color_hex": "#6C5CE7", "order_index": 27},
            {"name": "Electronics", "type": "Expense", "color_hex": "#2D3436",
             "order_index": 28},
            {"name": "Taxes", "type": "Expense", "color_hex": "#B33939",
             "order_index": 29},
            {"name": "Insurance", "type": "Expense", "color_hex": "#218C74",
             "order_index": 30},
            {"name": "Other Expenses", "type": "Expense",
             "color_hex": "#95A5A6", "order_index": 99},
            {"name": "Spent on donate", "type": "Expense",
             "color_hex": "#95A5A6", "order_index": 100},
            {"name": "Receive from saved", "type": "Income",
             "color_hex": "#95A5A6", "order_index": 101},
        ]

        count = 0
        for item in categories_data:
            obj, created = Category.objects.get_or_create(
                name=item["name"],
                defaults={
                    "category_type": item["type"],
                    "color_hex": item["color_hex"],
                    "order_index": item["order_index"]
                }
            )
            if created:
                count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully added {count} new categories"))
