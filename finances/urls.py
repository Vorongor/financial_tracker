from django.urls import path

from finances.views import (
    FinancesHomeView,
    BudgetUpdateView,
    TransferCreateView,
    TopUpBudgetView,
    TransactionListView,
    CategoryOptionsView, SetExpenseBudgetView,
)

urlpatterns = [
    path("", FinancesHomeView.as_view(), name="finances-home"),
    path(
        "personal-budget/<int:pk>/", BudgetUpdateView.as_view(),
        name="personal-budget"
    ),
    path(
        "transfer-create/<str:content_type>/<int:object_id>/",
        TransferCreateView.as_view(),
        name="transfer-create",
    ),
    path(
        "budget/top-up/",
        TopUpBudgetView.as_view(),
        name="budget-top-up"
    ),
    path(
        "budget/set-expebse/",
        SetExpenseBudgetView.as_view(),
        name="set-expense-budget"
    ),
    path(
        "<str:target>/history/<int:pk>/",
        TransactionListView.as_view(),
        name="transfer-history",
    ),
    path(
        'ajax/categories/',
        CategoryOptionsView.as_view(),
         name='ajax_get_categories'
    ),
]
