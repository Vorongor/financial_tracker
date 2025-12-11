from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView

from accounts.forms import UserRegisterForm


class RegisterView(CreateView):
    template_name = "registration/register.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy("dashboard:dashboard")


class ProfileView(DetailView):
    model = get_user_model()
    template_name = "profile/profile_detail.html"

