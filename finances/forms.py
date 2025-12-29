from decimal import Decimal

from django import forms
from django.forms import ModelForm

from finances.models import Budget, Transaction, Category


class UpdateBudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = [
            "current_amount",
            "start_amount",
            "planned_amount",
        ]

    def clean(self) -> None:
        cleaned_data = super(UpdateBudgetForm, self).clean()
        return cleaned_data


class TransferCreateForm(forms.ModelForm):
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )

    class Meta:
        model = Transaction
        fields = [
            "amount",
            "transaction_type",
            "category",
            "note",
        ]
        widgets = {
            "amount": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "step": "0.01"}
            ),
            "transaction_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "note": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Enter your note here",
                }
            ),
        }


class TopUpBudgetForm(forms.Form):
    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        label="Amount"
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2})
    )

    date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(category_type=Category.Types.INCOME),
        required=False,
        empty_label="Select Category (Optional)"
    )


class BudgetEditForm(ModelForm):
    class Meta:
        model = Budget
        fields = (
            "planned_amount",
            "start_amount",
        )
        widgets = {
            "planned_amount": forms.NumberInput(
                attrs={
                    "class": "form-control"}
            ),
            "start_amount": forms.NumberInput(
                attrs={
                    "class": "form-control"}
            ),
        }


class SetExpenseBudgetForm(forms.Form):
    amount = forms.DecimalField(
        min_value=Decimal("0.01"), max_digits=12, decimal_places=2,
        label="Amount"
    )
    note = forms.CharField(required=False,
                           widget=forms.Textarea(attrs={"rows": 2}))

    date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(category_type=Category.Types.EXPENSE),
        required=False,
        empty_label="Select Category (Optional)"
    )
