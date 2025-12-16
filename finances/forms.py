from decimal import Decimal

from django import forms

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

class TransferCreateForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            "amount",
            "type",
            "date",
            "category",
            "note",
        ]


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