from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from finances.models import Budget, Category, Transaction

User = get_user_model()


class FinancesViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="tester",
            password="1Qazcde3"
        )
        self.user_ct = ContentType.objects.get_for_model(User)
        self.budget = Budget.objects.get(
            content_type=self.user_ct,
            object_id=self.user.id,
        )
        self.budget.start_amount = Decimal("1000.00")
        self.budget.save()

        self.income_cat = Category.objects.create(
            name="Salary",
            type=Category.Types.INCOME
        )
        self.expense_cat = Category.objects.create(
            name="Food",
            type=Category.Types.EXPENSE
        )

        Category.objects.create(
            name="Spent on donate",
            type=Category.Types.EXPENSE
        )
        Category.objects.create(
            name="Receive from saved",
            type=Category.Types.INCOME
        )

        self.client.login(
            username="tester", password="1Qazcde3")

    def test_finances_home_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("finances-home"))
        self.assertEqual(response.status_code, 200)

    def test_top_up_budget_view_post(self):
        url = reverse("budget-top-up")
        data = {
            'amount': '500.00',
            'category': self.income_cat.id,
            'note': 'Test Top Up'
        }
        response = self.client.post(
            url,
            data,
            HTTP_REFERER=reverse("finances-home")
        )

        self.assertEqual(response.status_code, 302)
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.current_amount, Decimal("1500.00"))

    def test_transfer_create_view_to_another_user(self):
        other_user = User.objects.create_user(
            username="target_user",
            password="password"
        )
        other_budget = Budget.objects.get(
            content_type=self.user_ct,
            object_id=other_user.id
        )

        url = reverse(
            "transfer-create",
            kwargs={
                "content_type": "user",
                "object_id": other_user.id
            }
        )
        data = {
            "amount": "200.00",
            "type": "Expense",
            "category": self.expense_cat.id
        }

        response = self.client.post(
            url,
            data,
            HTTP_REFERER=reverse("finances-home")
        )

        self.assertEqual(response.status_code, 302)
        self.budget.refresh_from_db()
        other_budget.refresh_from_db()

        self.assertEqual(self.budget.current_amount, Decimal("800.00"))
        self.assertEqual(other_budget.current_amount, Decimal("200.00"))

    def test_transaction_list_view_htmx(self):
        Transaction.objects.create(
            amount=Decimal("10.00"),
            target=self.budget,
            payer=self.user,
            note="UniqueNote123"
        )

        url = reverse(
            "transfer-history",
            kwargs={'target': 'user', 'pk': self.user.id}
        )

        response = self.client.get(url)
        self.assertTemplateUsed(
            response,
            "transactions/transaction_list.html"
        )

        response = self.client.get(url, HTTP_HX_REQUEST='true')
        self.assertTemplateUsed(
            response,
            "partials/transaction_table_rows.html"
        )

        response = self.client.get(
            f"{url}?search=UniqueNote123",
            HTTP_HX_REQUEST='true'
        )

        response = self.client.get(
            f"{url}?search=Nothing",
            HTTP_HX_REQUEST='true'
        )
        self.assertNotContains(response, "UniqueNote123")

    def test_category_options_view_filter(self):
        url = reverse("ajax_get_categories")

        response = self.client.get(f"{url}?type=Income")
        self.assertContains(response, self.income_cat.name)
        self.assertNotContains(response, self.expense_cat.name)

        response = self.client.get(f"{url}?type=Expense")
        self.assertContains(response, self.expense_cat.name)
        self.assertNotContains(response, self.income_cat.name)
