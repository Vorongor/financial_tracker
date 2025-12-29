from urllib import request

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from accounts.models import Currency

User = get_user_model()


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
        ]

    username = forms.CharField(
        max_length=255, widget=forms.TextInput(
            attrs={"placeholder": "Username"})
    )

    email = forms.EmailField(
        max_length=255, widget=forms.EmailInput(
            attrs={"placeholder": "Email"})
    )

    first_name = forms.CharField(
        max_length=255, widget=forms.TextInput(
            attrs={"placeholder": "First name"})
    )

    last_name = forms.CharField(
        max_length=255, widget=forms.TextInput(
            attrs={"placeholder": "Last name"})
    )

    password1 = forms.CharField(
        label="Password", widget=forms.PasswordInput(
            attrs={"placeholder": "Password"})
    )

    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat password"}),
    )

    def clean_username(self) -> str:
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username


class UserUpdateForm(forms.ModelForm):
    default_currency = forms.ChoiceField(
        choices=Currency.choices,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "placeholder": "Currency (UAH, USD, EUR...)"
            }
        ),
    )

    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "job",
            "salary",
            "default_currency",
        ]


class UserKeyConnectForm(forms.Form):
    unik_key = forms.CharField(max_length=255, label="Unique key")
