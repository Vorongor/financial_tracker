from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    TemplateView,
    UpdateView,
    ListView,
)

from finances.models import Budget, Transaction, Category
from finances.forms import (
    UpdateBudgetForm,
    TransferCreateForm,
    TopUpBudgetForm, SetExpenseBudgetForm
)
from finances.services.history_service import TransactionHistoryService
from finances.services.transfers_service import TransfersService

User = get_user_model()


def get_back_url(instance) -> str:
    return reverse_lazy("profile-page",
                        kwargs={"pk": instance.request.user.pk})


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

    def post(self, request, content_type, object_id):
        form = TransferCreateForm(request.POST)

        if not form.is_valid():
            messages.error(request, "Invalid data")
            return redirect(request.META.get("HTTP_REFERER"))

        try:
            to_budget = TransfersService.get_budget_by_content_type(
                content_type,
                object_id
            )
            TransfersService.transfer_between_budgets(
                amount=form.cleaned_data["amount"],
                from_budget=request.user.budget,
                to_budget=to_budget,
                payer=request.user,
                date=form.cleaned_data.get("date") or timezone.now().date(),
                category=form.cleaned_data.get("category"),
                note=form.cleaned_data.get("note", ""),
            )
            messages.success(request, "Transaction created successfully")
        except ValueError as e:
            messages.error(request, str(e))

        return redirect(request.META.get("HTTP_REFERER"))


class TopUpBudgetView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = TopUpBudgetForm(request.POST)
        if form.is_valid():
            TransfersService.top_up_budget(
                user=request.user,
                amount=form.cleaned_data["amount"],
                category=form.cleaned_data.get("category"),
                note=form.cleaned_data.get("note", ""),
                date=form.cleaned_data.get("date") or timezone.now().date(),
            )
            return redirect(request.META.get("HTTP_REFERER", "/"))

        return redirect(request.META.get("HTTP_REFERER", "/"))


class SetExpenseBudgetView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = SetExpenseBudgetForm(request.POST)
        if form.is_valid():
            TransfersService.set_expense(
                user=request.user,
                amount=form.cleaned_data["amount"],
                category=form.cleaned_data.get("category"),
                note=form.cleaned_data.get("note", ""),
                date=form.cleaned_data.get("date") or timezone.now().date(),
            )
            return redirect(request.META.get("HTTP_REFERER", "/"))

        return redirect(request.META.get("HTTP_REFERER", "/"))


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transactions/transaction_list.html"
    context_object_name = "transaction_list"

    paginate_by = 20

    def get_queryset(self):
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
                Q(note__icontains=search) |
                Q(category__name__icontains=search)
            ).distinct()

        t_type = self.request.GET.get("type")
        if t_type in [Transaction.Types.INCOME, Transaction.Types.EXPENSE]:
            queryset = queryset.filter(type=t_type)

        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["target"] = self.kwargs.get("target")
        context["pk"] = self.kwargs.get("pk")
        return context

    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            return ["partials/transaction_table_rows.html"]
        return [self.template_name]


class CategoryOptionsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        transaction_type = kwargs.get('type') or request.GET.get('type')

        categories = Category.objects.filter(is_active=True)

        if transaction_type:
            categories = categories.filter(type=transaction_type).order_by(
                'order_index', 'name')

        return render(
            request,
            "partials/categories_to_form.html",
            {'categories': categories}
        )
