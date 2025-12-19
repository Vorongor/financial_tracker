from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    TemplateView,
    UpdateView,
    CreateView,
    ListView,
)

from events.models import Event
from finances.custom_mixins import SuccessUrlFromNextMixin
from finances.models import Budget, Transaction, Category
from finances.forms import UpdateBudgetForm, TransferCreateForm, TopUpBudgetForm
from finances.services.history_service import (
    get_user_transactions,
    get_event_transactions,
    get_group_transactions,
)
from finances.services.transfers_service import transfer_between_budgets
from groups.models import Group

User = get_user_model()


def get_back_url(instance) -> str:
    return reverse_lazy("profile-page", kwargs={"pk": instance.request.user.pk})


class FinancesHomeView(TemplateView):
    template_name = "finances-home.html"


class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    model = Budget
    form_class = UpdateBudgetForm
    template_name = "budget_form.html"

    def get_success_url(self):
        return get_back_url(self)


class TransferCreateView(
    LoginRequiredMixin,
    View,
):
    OWNER_MODELS = {
        "event": Event,
        "group": Group,
        "user": User,
    }

    def post(self, request, content_type, object_id):
        form = TransferCreateForm(request.POST)

        if not form.is_valid():
            messages.error(request, "Invalid data")
            return redirect(request.META.get("HTTP_REFERER"))

        user = request.user
        from_budget = user.budget
        to_budget = self.get_budget(content_type=content_type, object_id=object_id)
        date = form.cleaned_data.get("date") or timezone.now().date()

        transfer_between_budgets(
            amount=form.cleaned_data["amount"],
            from_budget=from_budget,
            to_budget=to_budget,
            payer=user,
            date=date,
            category=form.cleaned_data.get("category"),
            note=form.cleaned_data.get("note", ""),
        )

        messages.success(request, "Transaction created successfully")
        return redirect(request.META.get("HTTP_REFERER"))

    def get_budget(self, content_type, object_id):
        owner = self.get_owner(content_type, object_id)
        budget = owner.budget

        if not budget:
            raise ValueError("Target has no budget")

        return budget

    def get_owner(self, content_type, object_id):
        model = self.OWNER_MODELS.get(content_type)
        if not model:
            raise ValueError("Invalid owner type")

        return get_object_or_404(model, pk=object_id)


class TopUpBudgetView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = TopUpBudgetForm(request.POST)

        if not form.is_valid():
            return redirect(request.META.get("HTTP_REFERER", "/"))

        Transaction.objects.create(
            amount=form.cleaned_data["amount"],
            type=Transaction.Types.INCOME,
            target=request.user.budget,
            payer=request.user,
            date=timezone.now(),
            category=form.cleaned_data.get("category"),
            note=form.cleaned_data.get("note", ""),
        )

        request.user.budget.recalc()

        return redirect(request.META.get("HTTP_REFERER", "/"))


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transactions/transaction_list.html"

    def get_queryset(self):
        target = self.kwargs.get("target")
        pk = self.kwargs.get("pk")

        if target == "user":
            return get_user_transactions(self, pk)
        elif target == "event":
            return get_event_transactions(self, pk)
        elif target == "group":
            return get_group_transactions(self, pk)


class CategoryOptionsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        transaction_type = kwargs.get('type') or request.GET.get('type')

        categories = Category.objects.filter(is_active=True)

        if transaction_type:
            categories = categories.filter(type=transaction_type).order_by(
                'order_index', 'name')

        return render(request, "partials/categories_to_form.html", {
            'categories': categories
        })