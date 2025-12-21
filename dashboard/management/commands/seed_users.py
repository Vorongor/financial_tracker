import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from faker import Faker

User = get_user_model()


class Command(BaseCommand):
    help = "Generates 120 test users to validate the system"

    def handle(self, *args, **kwargs):
        fake = Faker(['en_US'])

        jobs = [
            "Software Engineer", "Project Manager", "Designer", "Data Analyst",
            "Builder", "Mechanic", "Military Servant", "Marketing Specialist",
            "Sales Manager", "Accountant", "Doctor", "Teacher", "HR Specialist",
            "Logistics Coordinator", "Architect",
            "Product Manager", "Business Analyst", "QA Engineer",
            "DevOps Engineer", "System Administrator", "Network Engineer",
            "Cybersecurity Specialist",
            "UX Researcher", "UI Designer", "Content Manager", "Copywriter",
            "SEO Specialist", "Digital Marketing Manager", "Brand Manager",
            "Financial Analyst", "Economist", "Auditor", "Investment Manager",
            "Bank Clerk", "Insurance Agent", "Risk Manager",
            "Lawyer", "Legal Advisor", "Paralegal",
            "Civil Engineer", "Electrical Engineer", "Mechanical Engineer",
            "Industrial Engineer", "Construction Manager",
            "Surveyor", "Urban Planner",
            "Real Estate Agent", "Property Manager",
            "Supply Chain Manager", "Procurement Specialist",
            "Operations Manager",
            "Customer Support Specialist", "Customer Success Manager",
            "Technical Support Engineer",
            "QA Tester", "Game Designer", "Game Developer",
            "Product Owner",
            "Scrum Master"
        ]

        self.stdout.write(f"We are starting to create 120 users...")

        try:
            with transaction.atomic():
                for i in range(120):
                    first_name = fake.first_name()
                    last_name = fake.last_name()

                    username = f"{fake.user_name()}_{i}"

                    user = User.objects.create(
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        email=fake.unique.email(),
                        job=random.choice(jobs),
                        salary=random.randint(15000, 150000),
                        default_currency=random.choice(["UAH", "USD", "EUR"]),
                    )
                    user.set_password("1Qazcde3")
                    user.save()

                    if (i + 1) % 100 == 0:
                        self.stdout.write(self.style.SUCCESS(
                            f"Created {i + 1} users..."))

            self.stdout.write(self.style.SUCCESS(
                "Successfully created 120 users with budgets!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error filling in: {e}"))
