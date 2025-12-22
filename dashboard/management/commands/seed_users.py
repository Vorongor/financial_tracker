import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from faker import Faker

User = get_user_model()


class Command(BaseCommand):
    help_tag = "Generates 120 test users to validate the system"

    def handle(self, *args, **kwargs):
        fake = Faker(["en_US"])

        # Список гарантованих користувачів для тестувальника
        test_users = [
            {"username": "admin_tester", "first_name": "Admin",
             "last_name": "Tester", "job": "QA Manager"},
            {"username": "dev_tester", "first_name": "Dev",
             "last_name": "Tester", "job": "Software Engineer"},
            {"username": "user_tester", "first_name": "Regular",
             "last_name": "User", "job": "Accountant"},
            {"username": "analyst_tester", "first_name": "Data",
             "last_name": "Analyst", "job": "Data Analyst"},
            {"username": "manager_tester", "first_name": "Project",
             "last_name": "Manager", "job": "Project Manager"},
        ]

        jobs = [
            "Software Engineer", "Project Manager", "Designer", "Data Analyst",
            "Builder", "Mechanic", "Military Servant", "Marketing Specialist",
            "Sales Manager", "Accountant", "Doctor", "Teacher",
            "HR Specialist",
            "Logistics Coordinator", "Architect", "Product Manager",
            "Business Analyst",
            "QA Engineer", "DevOps Engineer", "System Administrator",
            "Network Engineer",
            "Cybersecurity Specialist", "UX Researcher", "UI Designer",
            "Content Manager",
            "Copywriter", "SEO Specialist", "Digital Marketing Manager",
            "Brand Manager",
            "Financial Analyst", "Economist", "Auditor", "Investment Manager",
            "Bank Clerk", "Insurance Agent", "Risk Manager", "Lawyer",
            "Legal Advisor",
            "Paralegal", "Civil Engineer", "Electrical Engineer",
            "Mechanical Engineer",
            "Industrial Engineer", "Construction Manager", "Surveyor",
            "Urban Planner",
            "Real Estate Agent", "Property Manager", "Supply Chain Manager",
            "Procurement Specialist", "Operations Manager",
            "Customer Support Specialist",
            "Customer Success Manager", "Technical Support Engineer",
            "QA Tester",
            "Game Designer", "Game Developer", "Product Owner", "Scrum Master"
        ]

        self.stdout.write(
            "Starting to create 120 users (5 static + 115 random)...")

        try:
            with transaction.atomic():

                for u_data in test_users:
                    if not User.objects.filter(
                            username=u_data["username"]).exists():
                        user = User.objects.create(
                            username=u_data["username"],
                            first_name=u_data["first_name"],
                            last_name=u_data["last_name"],
                            email=f"{u_data['username']}@example.com",
                            job=u_data["job"],
                            salary=random.randint(50000, 100000),
                            default_currency="USD",
                        )
                        user.set_password(
                            "1Qazcde3")
                        user.save()

                self.stdout.write(
                    self.style.SUCCESS("Static test users created."))


                remaining_count = 120 - len(test_users)
                for i in range(remaining_count):
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

                    if (i + 1) % 50 == 0:
                        self.stdout.write(
                            f"Created {i + 1 + 5} users so far...")

            self.stdout.write(
                self.style.SUCCESS(f"Successfully created 120 users!"))
            self.stdout.write(
                self.style.WARNING("Test password for all: 1Qazcde3"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error filling in: {e}"))