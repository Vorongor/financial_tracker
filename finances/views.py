from typing import Any

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, QuerySet
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    TemplateView,
    UpdateView,
    ListView,
    DeleteView,
)

from finances.models import Budget, Transaction, Category
from finances.forms import (
    UpdateBudgetForm,
    TransferCreateForm,
    TopUpBudgetForm,
    SetExpenseBudgetForm
)
from finances.services.history_service import TransactionHistoryService
from finances.services.transfers_service import TransfersService

User = get_user_model()


def get_back_url(instance) -> HttpResponseRedirect:
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

    def get_success_url(self) -> HttpResponseRedirect:
        return get_back_url(self)


class BaseTransferActionView(LoginRequiredMixin, View):
    form_class = None

    def get_service_kwargs(
            self,
            form,
            request: HttpRequest,
            **kwargs
    ) -> dict[str, Any]:
        """Override this to pass specific data to the service method."""
        return {
            "amount": form.cleaned_data["amount"],
            "category": form.cleaned_data.get("category"),
            "note": form.cleaned_data.get("note", ""),
            "date": form.cleaned_data.get("date") or timezone.now().date(),
        }

    def execute_service(self, service_kwargs) -> None:
        """Override this to call the specific TransfersService method."""
        raise NotImplementedError("Subclasses must implement execute_service")

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        form = self.form_class(request.POST)

        if not form.is_valid():
            messages.error(request, "Invalid data")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        try:
            service_kwargs = self.get_service_kwargs(form, request, **kwargs)
            self.execute_service(service_kwargs)
            messages.success(
                request,
                "Transaction processed successfully"
            )
        except ValueError as e:
            messages.error(request, str(e))

        return redirect(request.META.get("HTTP_REFERER", "/"))


class TransferCreateView(BaseTransferActionView):
    form_class = TransferCreateForm

    def get_service_kwargs(
            self,
            form,
            request: HttpRequest,
            **kwargs
    ) -> dict[str, Any]:
        data = super().get_service_kwargs(form, request, **kwargs)
        data["to_budget"] = TransfersService.get_budget_by_content_type(
            kwargs['content_type'], kwargs['object_id']
        )
        data["from_budget"] = request.user.budget
        data["payer"] = request.user
        return data

    def execute_service(self, service_kwargs):
        TransfersService.transfer_between_budgets(**service_kwargs)


class TopUpBudgetView(BaseTransferActionView):
    form_class = TopUpBudgetForm

    def execute_service(self, service_kwargs) -> None:
        TransfersService.top_up_budget(
            user=self.request.user,
            **service_kwargs
        )


class SetExpenseBudgetView(BaseTransferActionView):
    form_class = SetExpenseBudgetForm

    def execute_service(self, service_kwargs) -> None:
        TransfersService.set_expense(user=self.request.user, **service_kwargs)


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transactions/transaction_list.html"
    context_object_name = "transaction_list"

    paginate_by = 20

    def get_queryset(self) -> QuerySet[Transaction]:
        target = self.kwargs.get("target")
        pk = self.kwargs.get("pk")

        if target == "user":
            queryset = TransactionHistoryService.get_user_transactions(
                user_id=pk
            )
        elif target == "event":
            queryset = TransactionHistoryService.get_event_transactions(
                event_id=pk
            )
        elif target == "group":
            queryset = TransactionHistoryService.get_group_transactions(
                group_id=pk
            )
        else:
            return Transaction.objects.none()

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(note__icontains=search)
                | Q(category__name__icontains=search)
            ).distinct()

        t_type = self.request.GET.get("type")
        if t_type in [Transaction.Types.INCOME, Transaction.Types.EXPENSE]:
            queryset = queryset.filter(transaction_type=t_type)

        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        return queryset

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["target"] = self.kwargs.get("target")
        context["pk"] = self.kwargs.get("pk")
        return context

    def get_template_names(self) -> list[str]:
        if self.request.headers.get("HX-Request"):
            return ["partials/transaction_table_rows.html"]
        return [self.template_name]


class CategoryOptionsView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        category_type = (kwargs.get("transaction_type")
                         or request.GET.get("transaction_type"))

        categories = Category.objects.filter(is_active=True)

        if category_type:
            categories = categories.filter(
                category_type=category_type
            ).order_by(
                "order_index", "name")

        return render(
            request,
            "partials/categories_to_form.html",
            {"categories": categories}
        )


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction

    def get_success_url(self) -> HttpResponseRedirect:
        return reverse_lazy(
            "transfer-history",
            kwargs={"target": "user", "pk": self.request.user.pk}
        )
