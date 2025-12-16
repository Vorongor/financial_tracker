from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    TemplateView,
    CreateView,
    DetailView,
    DeleteView,
)

from accounts.services.receive_connection import get_user_connections
from addition_info.choise_models import Status, Role
from finances.custom_mixins import SuccessUrlFromNextMixin
from groups.forms import GroupCreateForm
from groups.models import Group, GroupMembership
from groups.services.group_invitation import create_group_invitation, \
    accept_group_invitation, reject_group_invitation


class GroupsHomeView(LoginRequiredMixin, TemplateView):
    template_name = "groups-home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        groups = Group.objects.filter(
            Q(creator=user) |
            Q(groupslink__user=user,
              groupslink__status=Status.ACCEPTED)
        ).distinct()
        context["groups"] = groups

        context["invites"] = GroupMembership.objects.filter(
            user_id=user.id,
            status=Status.PENDING,
        )
        return context


class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupCreateForm
    success_url = reverse_lazy("groups-home")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()

        GroupMembership.objects.create(
            group=self.object,
            user=self.request.user,
            status=Status.ACCEPTED,
            role=Role.ADMIN,
        )

        participants_ids = form.cleaned_data["participants"]

        create_group_invitation(
            list_of_connects=participants_ids,
            group_id=self.object.id
        )

        return super().form_valid(form)


class GroupDetailView(
    LoginRequiredMixin,
    SuccessUrlFromNextMixin,
    DetailView,
):
    model = Group
    fields = "__all__"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        transaction_history = self.object.budget.transactions.all()
        members = GroupMembership.objects.filter(group_id=self.object.id)
        users = [
            connect.other_user(user)
            for connect in get_user_connections(
                user.id,
                "accepted"
            )
            if connect.other_user(user).id not in members.values_list(
                "user__id",
                flat=True
            )
        ]

        context["transaction_history"] = transaction_history
        context["current_budget"] = self.object.budget.get_budget_data()
        context["connects"] = users
        context["members"] = members
        return context


class GroupDeleteView(LoginRequiredMixin, DeleteView):
    model = Group
    success_url = reverse_lazy("groups-home")


class GroupInviteMemberView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id):
        group = get_object_or_404(Group, pk=pk)

        if not group:
            raise ValidationError("Group not found")

        create_group_invitation(
            group_id=group.id,
            list_of_connects=[user_id,]
        )
        return redirect("group-detail", pk=pk)


class GroupAcceptInviteView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id):
        group = get_object_or_404(Group, pk=pk)

        if not group:
            raise ValidationError("Group not found")

        accept_group_invitation(group_id=group.id, user_id=user_id)
        return redirect("groups-home")


class GroupRejectInviteView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id, stay):
        group = get_object_or_404(Group, pk=pk)

        if not group:
            raise ValidationError("Group not found")

        reject_group_invitation(group_id=group.id, user_id=user_id)

        if stay == "inside":
            return redirect("group-detail", pk=pk)
        else:
            return redirect("groups-home")
