from django import forms
from django.forms import ModelForm

from accounts.services.receive_connection import get_user_connections
from groups.models import Group


class GroupCreateForm(ModelForm):
    participants = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Group
        fields = (
            "name",
            "description",
            "state",
            "start_date",
            "end_date")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        connections = get_user_connections(user.id, "accepted")

        self.fields["participants"].choices = [
            (c.other_user(user).id, c.other_user(user).username)
            for c in connections
        ]

