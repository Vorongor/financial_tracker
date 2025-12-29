from django import forms
from django.forms import ModelForm

from accounts.services.receive_connection import UserConnectionsService
from .models import Event


class EventPrivateCreateForm(forms.ModelForm):
    participants = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    class Meta:
        model = Event
        fields = [
            "name",
            "description",
            "start_date",
            "end_date",
            "planned_amount",
            "event_type",
            "accessibility",
            "status",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Event name"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Optional description",
                }
            ),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "planned_amount": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "step": "0.01"}
            ),
            "event_type": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "accessibility": forms.Select(
                attrs={"class": "form-select"},
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        self.group = kwargs.pop("group", None)
        super().__init__(*args, **kwargs)

        connections = UserConnectionsService.get_user_connections(
            user.id,
            "accepted"
        )

        self.fields["participants"].choices = [
            (
                c.other_user(user).id,
                c.other_user(user).username) for c in connections
        ]

    def clean(self) -> None:
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date", None)
        end_date = cleaned_data.get("end_date", None)
        planned_amount = cleaned_data.get("planned_amount")
        event_type = cleaned_data.get("event_type")

        if (event_type == Event.EventType.EXPENSES
                or event_type == Event.EventType.ACCUMULATIVE):
            if planned_amount is not None and planned_amount <= 0:
                raise forms.ValidationError(
                    "Planned amount must be greate than zero"
                )
            if start_date is None:
                raise forms.ValidationError(
                    "You must provide start and end date for planning Expenses"
                )
            if end_date is None:
                raise forms.ValidationError(
                    "You must provide start and end date for planning Expenses"
                )

            if start_date and end_date and start_date > end_date:
                raise forms.ValidationError(
                    "End date cannot be earlier than start date."
                )

        return cleaned_data

    def save(self, commit: bool = True) -> Event:
        event = super().save(commit=False)
        if commit:
            event.save()
        return event


class EventEditForm(ModelForm):
    class Meta:
        model = Event
        fields = (
            "name",
            "description",
            "start_date",
            "end_date",
            "status",
            "event_type",
        )
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Event name"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Optional description",
                }
            ),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "event_type": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),

        }
