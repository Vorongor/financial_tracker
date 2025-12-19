from decimal import Decimal

from django import forms
from django.forms import ModelForm

from finances.models import Budget, Transaction


class UpdateBudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = [
            "current_amount",
            "start_amount",
            "planned_amount",
        ]

    def clean(self):
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
            "type",
            "category",
            "note",
        ]
        widgets = {
            "amount": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "step": "0.01"}
            ),
            "type": forms.Select(
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
        min_value=Decimal("0.01"), max_digits=12, decimal_places=2, label="Amount"
    )
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))


class BudgetEditForm(ModelForm):
    class Meta:
        model = Budget
        fields = (
            "planned_amount",
            "start_amount",
        )
