from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView, ListView

from accounts.forms import UserRegisterForm, UserUpdateForm, UserKeyConnectForm
from accounts.models import UserConnection
from accounts.services.receive_connection import get_user_connections
from accounts.services.user_connection_control import invite_user_to_connect, \
    approve_user_to_connect, reject_user_to_connect
from events.models import Event
from finances.forms import TopUpBudgetForm
from groups.models import Group


class RegisterView(CreateView):
    template_name = "registration/register.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy("dashboard:personal-dash")


class ProfileView(LoginRequiredMixin, DetailView):
    model = get_user_model()
    template_name = "profile/profile_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.object

        context["events"] = Event.objects.filter(
            Q(creator=user) | Q(memberships__user=user)
        ).distinct()

        context["groups"] = Group.objects.filter(
            Q(creator=user) | Q(groupslink__user=user)
        ).distinct()

        context["connections"] = get_user_connections(user.id, "accepted")

        context["take_to_connect"] = UserConnection.objects.filter(
            from_user=user, status=UserConnection.Status.PENDING
        ).distinct()

        context["invite_to_connect"] = UserConnection.objects.filter(
            to_user=user, status=UserConnection.Status.PENDING
        ).distinct()

        context["top_up_form"] = TopUpBudgetForm()
        context["transaction_history"] = self.object.budget.transactions.all()
        context["current_budget"] = self.object.budget.get_budget_data()

        return context


class UpdateProfileView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UserUpdateForm
    template_name = "profile/update_form.html"

    def get_success_url(self):
        return reverse_lazy(
            "profile-page",
            kwargs={"pk": self.object.pk}
        )


class CommunityListView(LoginRequiredMixin, ListView):
    model = get_user_model()
    template_name = "community/community_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        querySet = get_user_model().objects.exclude(
            pk=self.request.user.id
        )

        fried_list = get_user_connections(self.request.user.id)

        fried_list = ([connect.from_user.id for connect in fried_list]
                      + [connect.to_user.id for connect in fried_list])

        querySet = querySet.exclude(pk__in=fried_list)

        query = self.request.GET.get("q")
        if query:
            querySet = querySet.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )

        return querySet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["uniq_key_form"] = UserKeyConnectForm()
        context["connections"] = get_user_connections(self.request.user.id)

        return context


class UserConnectView(LoginRequiredMixin, View):
    def post(self, request, user_id):
        recipient = get_object_or_404(get_user_model(), pk=user_id)

        if recipient == request.user:
            return redirect("community-list")

        invite_user_to_connect(
            sender=request.user,
            recipient=recipient
        )

        return redirect(request.META.get("HTTP_REFERER", "community-list"))


class UserConnectApproveView(LoginRequiredMixin, View):
    def post(self, request, connection_id):
        approve_user_to_connect(
            connection_id=connection_id
        )

        return redirect(request.META.get("HTTP_REFERER", "profile-dashboard"))


class UserConnectRejectView(LoginRequiredMixin, View):
    def post(self, request, connection_id):
        reject_user_to_connect(
            connection_id=connection_id
        )

        return redirect(request.META.get("HTTP_REFERER", "profile-dashboard"))

