from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    UpdateView,
    ListView,
    DeleteView,
)

from accounts.forms import (
    UserRegisterForm,
    UserUpdateForm,
    UserKeyConnectForm
)
from accounts.models import UserConnection
from accounts.services.receive_connection import (
    get_user_connections,
    get_user_from_uk,
)
from accounts.services.user_connection_control import (
    invite_user_to_connect,
    approve_user_to_connect,
    reject_user_to_connect,
    block_user_to_connect,
    un_block_user_connect,
)
from events.models import Event
from events.services.event_invitation import create_event_invitation
from finances.forms import TopUpBudgetForm
from finances.models import Budget
from groups.models import Group
from groups.services.group_invitation import create_group_invitation


class RegisterView(CreateView):
    template_name = "registration/register.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            "Registration successful. Please log in.",
            extra_tags="registration",
        )
        return redirect(self.success_url)


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
        return reverse_lazy("profile-page", kwargs={"pk": self.object.pk})


class DeleteProfileView(LoginRequiredMixin, DeleteView):
    model = get_user_model()
    template_name = "profile/user_confirm_delete.html"
    success_url = reverse_lazy("login")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        ct = ContentType.objects.get_for_model(self.object)
        Budget.objects.get(owner_type=ct, owner_id=self.object.id).delete()

        messages.success(
            request,
            "Profile has been deleted. Please log in.",
            extra_tags="registration",
        )

        return super().delete(request, *args, **kwargs)


class CommunityListView(LoginRequiredMixin, ListView):
    model = get_user_model()
    template_name = "community/community_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        queryset = get_user_model().objects.exclude(pk=self.request.user.id)

        friend_list = get_user_connections(self.request.user.id)

        friend_list = [connect.from_user.id for connect in friend_list] + [
            connect.to_user.id for connect in friend_list
        ]

        queryset = queryset.exclude(pk__in=friend_list)

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        friend_list = get_user_connections(self.request.user.id)
        context["connections"] = [
            connect
            for connect in friend_list
            if connect.status == UserConnection.Status.ACCEPTED
        ]
        context["invite_to_connect"] = [
            connect
            for connect in friend_list
            if (connect.to_user == self.request.user
                and connect.status == UserConnection.Status.PENDING)
        ]
        context["sends_to_connect"] = [
            connect
            for connect in friend_list
            if (connect.from_user == self.request.user
                and connect.status == UserConnection.Status.PENDING)
        ]
        context["black_list"] = [
            connect
            for connect in friend_list
            if (connect.status == UserConnection.Status.BLOCKED
                and connect.from_user != self.request.user)
        ]
        context["uniq_key_form"] = UserKeyConnectForm()
        context["content_type"] = "connection"
        context["object_id"] = self.request.user.id

        return context


class UserConnectView(LoginRequiredMixin, View):
    def post(self, request, user_id):
        recipient = get_object_or_404(get_user_model(), pk=user_id)

        if recipient == request.user:
            return redirect("community-list")

        invite_user_to_connect(sender=request.user, recipient=recipient)

        return redirect(request.META.get("HTTP_REFERER", "community-list"))


class UserConnectApproveView(LoginRequiredMixin, View):
    def post(self, request, connection_id):
        approve_user_to_connect(connection_id=connection_id)

        return redirect(request.META.get("HTTP_REFERER", "profile-dashboard"))


class UserConnectRejectView(LoginRequiredMixin, View):
    def post(self, request, connection_id):
        reject_user_to_connect(connection_id=connection_id)

        return redirect(request.META.get("HTTP_REFERER", "profile-dashboard"))


class UserConnectBlockView(LoginRequiredMixin, View):
    def post(self, request, connection_id):
        block_user_to_connect(connection_id=connection_id)

        return redirect(request.META.get("HTTP_REFERER", "profile-dashboard"))


class UserConnectUnblockView(LoginRequiredMixin, View):
    def post(self, request, connection_id):
        un_block_user_connect(connection_id=connection_id)

        return redirect(
            request.META.get("HTTP_REFERER", "profile-dashboard")
        )


class UserUkConnectView(LoginRequiredMixin, View):
    def post(self, request, invite_type, sender_id):
        form = UserKeyConnectForm(request.POST)

        if not form.is_valid():
            messages.error(
                request,
                "Invalid key format",
                extra_tags="community"
            )
            return redirect(request.META.get("HTTP_REFERER"))

        unik_key = form.data.get("unik_key")

        try:
            recipient = get_user_from_uk(unik_key)
            if invite_type == "connection":
                invite_user_to_connect(sender=request.user,
                                       recipient=recipient)
            elif invite_type == "event":
                create_event_invitation(
                    list_of_connects=[
                        recipient.id,
                    ],
                    event_id=sender_id,
                )
            elif invite_type == "group":
                create_group_invitation(
                    list_of_connects=[
                        recipient.id,
                    ],
                    group_id=sender_id,
                )
            messages.success(
                request, "Connection request sent successfully.",
                extra_tags="community"
            )
        except ValidationError as e:
            messages.error(request, e.message, extra_tags="community")
        except get_user_model().DoesNotExist:
            messages.error(request, "User not found.", extra_tags="community")

        return redirect(request.META.get("HTTP_REFERER", "profile-dashboard"))
