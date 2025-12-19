from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
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
from events.models import Event
from finances.custom_mixins import SuccessUrlFromNextMixin
from finances.forms import TransferCreateForm, BudgetEditForm
from groups.forms import GroupCreateForm, GroupEditForm, GroupEventCreateForm
from groups.models import Group, GroupMembership, GroupEventConnection
from groups.services.group_event_service import create_group_event, get_events_for_group
from groups.services.group_invitation import (
    create_group_invitation,
    accept_group_invitation,
    reject_group_invitation,
    promote_group_member,
    demote_group_member,
    leave_group,
)


class GroupsHomeView(LoginRequiredMixin, TemplateView):
    template_name = "groups-home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        groups = Group.objects.filter(
            Q(creator=user)
            | Q(groupslink__user=user, groupslink__status=Status.ACCEPTED)
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
    success_url = reverse_lazy("groups:home")

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
            role=Role.CREATOR,
        )

        participants_ids = form.cleaned_data["participants"]

        create_group_invitation(
            list_of_connects=participants_ids, group_id=self.object.id
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
        group = self.object
        user = self.request.user
        transaction_history = group.budget.transactions.all()
        members = GroupMembership.objects.filter(group_id=group.id)
        users = [
            connect.other_user(user)
            for connect in get_user_connections(user.id, "accepted")
            if connect.other_user(user).id
            not in members.values_list("user__id", flat=True)
        ]
        user_role = members.filter(user=user).first().role
        delete_permission = "Creator" if group.creator else "Admin"
        context["related_events"] = get_events_for_group(group_id=group.id)
        context["transaction_history"] = transaction_history
        context["current_budget"] = self.object.budget.get_budget_data()
        context["delete_permission"] = delete_permission
        context["transaction_form"] = TransferCreateForm()
        context["content_type"] = "group"
        context["object_id"] = group.id
        context["user_role"] = user_role
        context["connects"] = users
        context["members"] = members
        return context


class GroupEditView(LoginRequiredMixin, View):
    template_name = "groups/group_update.html"

    def get(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        budget = group.budget

        return render(
            request,
            self.template_name,
            {
                "group_form": GroupEditForm(instance=group),
                "budget_form": BudgetEditForm(instance=budget),
                "group": group,
            },
        )

    @transaction.atomic
    def post(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        budget = group.budget

        group_form = GroupEditForm(request.POST, instance=group)
        budget_form = BudgetEditForm(request.POST, instance=budget)

        if group_form.is_valid() and budget_form.is_valid():
            group_form.save()
            budget_form.save()
            budget.recalc()
            return redirect("groups:detail", pk=pk)

        return render(
            request,
            self.template_name,
            {
                "group_form": group_form,
                "budget_form": budget_form,
                "group": group,
            },
        )


class GroupDeleteView(LoginRequiredMixin, DeleteView):
    model = Group
    success_url = reverse_lazy("groups:home")


class GroupInviteMemberView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id):
        group = get_object_or_404(Group, pk=pk)

        if not group:
            raise ValidationError("Group not found")

        create_group_invitation(
            group_id=group.id,
            list_of_connects=[
                user_id,
            ],
        )
        return redirect("groups:detail", pk=pk)


class GroupAcceptInviteView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id):
        group = get_object_or_404(Group, pk=pk)

        if not group:
            raise ValidationError("Group not found")

        accept_group_invitation(group_id=group.id, user_id=user_id)
        return redirect("groups:home")


class GroupRejectInviteView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id, stay):
        group = get_object_or_404(Group, pk=pk)

        if not group:
            raise ValidationError("Group not found")

        reject_group_invitation(group_id=group.id, user_id=user_id)

        if stay == "inside":
            return redirect("groups:detail", pk=pk)
        else:
            return redirect("groups:home")


class GroupPromoteView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id):
        group = get_object_or_404(Group, pk=pk)

        if not group:
            raise ValidationError("Group not found")

        promote_group_member(group_id=group.id, user_id=user_id)
        return redirect("groups:detail", pk=pk)


class GroupDemoteView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id):
        group = get_object_or_404(Group, pk=pk)

        if not group:
            raise ValidationError("Group not found")

        demote_group_member(group_id=group.id, user_id=user_id)
        return redirect("groups:detail", pk=pk)


class LeaveGroupView(LoginRequiredMixin, View):
    def post(self, request, group_id):
        leave_group(group_id=group_id, user_id=request.user.id)
        return redirect("groups:home")


class GroupEventsCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = GroupEventCreateForm
    template_name = "groups/group-event_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(Group, pk=kwargs["group_id"])

        if not GroupMembership.objects.filter(
            group=self.group, user=request.user, status=Status.ACCEPTED
        ).exists():
            raise ValidationError("You are not a member of this group")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["group"] = self.group
        return kwargs

    def form_valid(self, form):
        event = form.save(commit=False)
        event.creator = self.request.user
        event.accessibility = Event.Accessibility.GROUP
        event.save()

        with transaction.atomic():
            event = create_group_event(
                group=self.group,
                event=event,
            )
        return redirect("groups:detail", pk=self.group.id)
