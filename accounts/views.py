from typing import Any

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse
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
from accounts.services.receive_connection import UserConnectionsService
from accounts.services.user_budget_service import UserBudgetService
from accounts.services.user_connection_control import UserInvitationService
from events.models import Event
from events.services.event_invitation import EventInvitationService
from finances.forms import TopUpBudgetForm
from finances.models import Budget, Category
from groups.models import Group
from groups.services.group_invitation import GroupInvitationService


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

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.object

        user_budget = user.budget

        context["transaction_history"] = (
            user_budget.transactions
            .select_related("category", "payer")
            .order_by("-date", "-timestamp_create")[:15]
        )

        context["current_budget"] = user_budget.get_budget_data()

        context["events"] = (
            Event.objects.filter(
                Q(creator=user) | Q(memberships__user=user)
            )
            .select_related("creator")
            .prefetch_related("memberships__user")
            .distinct()
        )

        context["groups"] = (
            Group.objects.filter(
                Q(creator=user) | Q(memberships__user=user)
            )
            .select_related("creator")
            .prefetch_related("memberships__user")
            .distinct()
        )

        context["take_to_connect"] = (
            UserConnection.objects.filter(
                from_user=user,
                status=UserConnection.Status.PENDING
            )
            .select_related("to_user")
        )

        context["invite_to_connect"] = (
            UserConnection.objects.filter(
                to_user=user,
                status=UserConnection.Status.PENDING
            )
            .select_related("from_user")
        )

        context["connections"] = UserConnectionsService.get_user_connections(
            user.id,
            "accepted"
        )

        categories = list(
            Category.objects.filter(is_active=True)
            .order_by("order_index", "name")
        )

        context["categories_income"] = [
            c for c in categories if c.category_type == Category.Types.INCOME
        ]
        context["categories_expense"] = [
            c for c in categories if c.category_type == Category.Types.EXPENSE
        ]

        context["top_up_form"] = TopUpBudgetForm()

        return context


class UpdateProfileView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UserUpdateForm
    template_name = "profile/update_form.html"

    def get_success_url(self) -> str:
        return reverse_lazy("profile-page", kwargs={"pk": self.object.pk})


class DeleteProfileView(LoginRequiredMixin, DeleteView):
    model = get_user_model()
    template_name = "profile/user_confirm_delete.html"
    success_url = reverse_lazy("login")

    def delete(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        messages.success(
            request,
            "Profile has been deleted. Please log in.",
            extra_tags="registration",
        )
        UserBudgetService.delete_user_budget(self.object)
        return super().delete(request, *args, **kwargs)


class CommunityListView(LoginRequiredMixin, ListView):
    model = get_user_model()
    template_name = "community/community_list.html"
    context_object_name = "other_users"

    def get_template_names(self) -> str:
        if self.request.headers.get("HX-Request"):
            return "partials/user_table_rows.html"
        return self.template_name

    def get_queryset(self) -> QuerySet[UserConnection]:
        query = self.request.GET.get("q", "")
        self.request.GET.get("status", "")

        connections = UserConnectionsService.get_user_connections(
            self.request.user.id)
        connected_ids = [
            c.from_user_id
            if c.to_user_id == self.request.user.id else c.to_user_id
            for c in connections
        ]
        connected_ids.append(self.request.user.id)

        queryset = get_user_model().objects.exclude(id__in=connected_ids)

        if query:
            queryset = queryset.filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        query = self.request.GET.get("q", "")
        status_filter = self.request.GET.get("status", "")

        connections = UserConnectionsService.get_user_connections(
            user_id=self.request.user.id,
            status=status_filter or None,
            query=query or None,
        )

        context["user_connections"] = connections
        context["status_choices"] = UserConnection.Status.choices
        context["uniq_key_form"] = UserKeyConnectForm()
        context["content_type"] = "connection"
        context["object_id"] = self.request.user.id

        return context


class UserConnectView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, user_id: int) -> HttpResponse:
        recipient = get_object_or_404(get_user_model(), pk=user_id)

        if recipient == request.user:
            return redirect("community-list")

        UserInvitationService.invite_user_to_connect(
            sender=request.user,
            recipient=recipient
        )

        return redirect(request.META.get("HTTP_REFERER", "community-list"))


class UserConnectApproveView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, connection_id: int) -> HttpResponse:
        UserInvitationService.approve_user_to_connect(
            connection_id=connection_id
        )
        return redirect(request.META.get("HTTP_REFERER", "/"))


class UserConnectRejectView(LoginRequiredMixin, View):
    def post(self, request:HttpRequest, connection_id: int) -> HttpResponse:
        UserInvitationService.reject_user_to_connect(
            connection_id=connection_id
        )

        return redirect(request.META.get("HTTP_REFERER", "profile-dashboard"))


class UserConnectBlockView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, connection_id: int) -> HttpResponse:
        UserInvitationService.block_user_to_connect(
            connection_id=connection_id
        )

        return redirect(request.META.get("HTTP_REFERER", "profile-dashboard"))


class UserConnectUnblockView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, connection_id: int) -> HttpResponse:
        UserInvitationService.un_block_user_connect(
            connection_id=connection_id
        )

        return redirect(
            request.META.get("HTTP_REFERER", "profile-dashboard")
        )


class UserUkConnectView(LoginRequiredMixin, View):
    def post(
            self,
            request: HttpRequest,
            invite_type: str,
            sender_id: int
    ) -> HttpResponse:
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
            recipient = UserConnectionsService.get_user_from_uk(
                unik_key
            )
            if invite_type == "connection":
                UserInvitationService.invite_user_to_connect(
                    sender=request.user,
                    recipient=recipient
                )
            elif invite_type == "event":
                EventInvitationService.create_event_invitation(
                    list_of_connects=[
                        recipient.id,
                    ],
                    event_id=sender_id,
                )
            elif invite_type == "group":
                GroupInvitationService.create_group_invitation(
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
            messages.error(request,
                           "User not found.",
                           extra_tags="community"
                           )

        return redirect(request.META.get("HTTP_REFERER", "/"))
