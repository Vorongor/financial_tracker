from urllib import request

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegisterForm(UserCreationForm):
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

    username = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Username"})
    )

    email = forms.EmailField(
        max_length=255,
        widget=forms.EmailInput(attrs={"placeholder": "Email"})
    )

    first_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "First name"})
    )

    last_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Last name"})
    )

    job = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Job"})
    )

    salary = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "Salary"})
    )

    default_currency = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Currency (UAH, USD, EUR...)"})
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )

    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat password"})
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("User with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username


class UserUpdateForm(forms.ModelForm):
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
    key = forms.CharField(
        max_length=255,
        label="Unique key"
    )
