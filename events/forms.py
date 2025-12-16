from django import forms

from accounts.services.receive_connection import get_user_connections
from .models import Event


class EventPrivateCreateForm(forms.ModelForm):
    participants = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Event
        fields = [
            "name",
            "description",
            "start_date",
            "end_date",
            "planned_amount",
            "type",
            "accessibility",
            "status",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Event name"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Optional description"
            }),
            "start_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "end_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "planned_amount": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
                "step": "0.01"
            }),
            "type": forms.Select(attrs={
                "class": "form-select"
            }),
            "status": forms.Select(attrs={
                "class": "form-select"
            }),
            "accessibility": forms.Select(attrs={
                "class": "form-select"
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        connections = get_user_connections(user.id, "accepted")

        self.fields["participants"].choices = [
            (c.other_user(user).id, c.other_user(user).username)
            for c in connections
        ]

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        planned_amount = cleaned_data.get("planned_amount")

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(
                "End date cannot be earlier than start date."
            )

        if planned_amount is not None and planned_amount < 0:
            raise forms.ValidationError(
                "Planned amount must be zero or positive."
            )
        return cleaned_data

    def save(self, commit = True):
        event = super().save(commit=False)
        if commit:
            event.save()
        return event
