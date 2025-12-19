from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    TemplateView,
    UpdateView,
    CreateView, ListView,
)

from events.models import Event
from finances.custom_mixins import SuccessUrlFromNextMixin
from finances.models import Budget, Transaction
from finances.forms import UpdateBudgetForm, TransferCreateForm, \
    TopUpBudgetForm
from finances.services.transfers_service import transfer_between_budgets
from groups.models import Group

User = get_user_model()


def get_back_url(instance) -> str:
    return reverse_lazy(
        "profile-page",
        kwargs={"pk": instance.request.user.pk}
    )


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
    View, ):
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
        to_budget = self.get_budget(
            content_type=content_type,
            object_id=object_id
        )
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

    TARGET_HANDLERS = {
        "user": "get_user_transactions",
        "event": "get_event_transactions",
        "group": "get_group_transactions",
    }

    def get_queryset(self):
        target = self.kwargs.get("target")
        pk = self.kwargs.get("pk")

        handler_name = self.TARGET_HANDLERS.get(target)
        if not handler_name:
            raise Http404("Invalid target")

        handler = getattr(self, handler_name)
        return handler(pk)
