from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    TemplateView,
    CreateView,
    DetailView,
    DeleteView,
)
from accounts.services.receive_connection import UserConnectionsService
from addition_info.choise_models import Status, Role
from dashboard.services.event_stats import EventAnalyticsService
from events.forms import EventPrivateCreateForm, EventEditForm
from events.models import Event, EventMembership
from events.services.event_invitation import EventInvitationService
from finances.forms import TransferCreateForm, BudgetEditForm
from finances.models import Budget


class EventHeroView(LoginRequiredMixin, TemplateView):
    template_name = "events/events_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["invites"] = EventMembership.objects.filter(
            user_id=self.request.user.id,
            status=Status.PENDING,
        )
        context["private_events"] = Event.objects.filter(
            creator=self.request.user,
            accessibility=Event.Accessibility.PRIVATE
        )
        context["public_events"] = Event.objects.filter(
            memberships__user=self.request.user,
            accessibility=Event.Accessibility.PUBLIC,
            memberships__status=Status.ACCEPTED,
        )
        context["group_events"] = Event.objects.filter(
            memberships__user=self.request.user,
            accessibility=Event.Accessibility.GROUP,
            memberships__status=Status.ACCEPTED,
        )

        return context


class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventPrivateCreateForm
    template_name = "events/event_form.html"
    success_url = "events:event-hero"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user

        accessibility = form.cleaned_data.get("accessibility")

        if accessibility == "Private":
            self.object.accessibility = self.object.Accessibility.PRIVATE
        if accessibility == "Public":
            self.object.accessibility = self.object.Accessibility.PUBLIC
        self.object.save()

        EventMembership.objects.create(
            event=self.object,
            user=self.request.user,
            status=Status.ACCEPTED,
            role=Role.CREATOR,
        )

        participants_ids = list(
            map(int, form.cleaned_data.get("participants", []))
        )
        EventInvitationService.create_event_invitation(
            list_of_connects=participants_ids, event_id=self.object.id
        )

        return redirect(self.get_success_url())


class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        budget = event.budget
        user = self.request.user

        members_qs = EventMembership.objects.filter(
            event=event
        ).select_related("user")

        user_membership = next((
            member
            for member in members_qs
            if member.user_id == user.id),
            None
        )
        user_role = user_membership.role if user_membership else None

        member_ids = set(members_qs.values_list("user_id", flat=True))

        potential_invites = []
        for connect in UserConnectionsService.get_user_connections(
                user.id,
                "accepted"
        ):
            other_user = connect.other_user(user)
            if other_user.id not in member_ids:
                potential_invites.append(other_user)
        delete_pos = ((event.creator_id == user.id)
                      or (not event.creator and user_role == "Admin"))
        try:
            budget = event.budget
            context["current_budget"] = budget.get_budget_data()
            context[
                "transaction_history"] = budget.transactions.select_related(
                "category", "payer"
            ).all()
        except AttributeError:
            context["current_budget"] = None
            context["transaction_history"] = []

        context.update({
            "can_delete_event": delete_pos,
            "transaction_form": TransferCreateForm(),
            "content_type": "event",
            "object_id": event.id,
            "user_role": user_role,
        })
        context["analytics"] = EventAnalyticsService.get_event_stats(
            event,
            budget,
        )
        context["social_analytics"] = EventAnalyticsService.get_social_stats(
            event, budget)
        if event.accessibility == Event.Accessibility.PRIVATE:
            context["connects"] = []
            context["members"] = []
        else:
            context["connects"] = potential_invites
            context["members"] = members_qs

        return context


class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = Event
    success_url = reverse_lazy("events:event-hero")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        ct = ContentType.objects.get_for_model(self.object)
        Budget.objects.get(owner_type=ct, owner_id=self.object.id).delete()

        return super().delete(request, *args, **kwargs)


class EventUpdateView(LoginRequiredMixin, View):
    template_name = "events/event_edit.html"

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        budget = event.budget

        return render(
            request,
            self.template_name,
            {
                "event_form": EventEditForm(instance=event),
                "budget_form": BudgetEditForm(instance=budget),
                "event": event,
            },
        )

    @transaction.atomic
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        budget = event.budget

        event_form = EventEditForm(request.POST, instance=event)
        budget_form = BudgetEditForm(request.POST, instance=budget)

        if event_form.is_valid() and budget_form.is_valid():
            event_form.save()
            budget_form.save()
            budget.recalc()

            event.planned_amount = budget.planned_amount
            event.save()

            return redirect("events:event-detail", pk=pk)

        return render(
            request,
            self.template_name,
            {
                "event_form": event_form,
                "budget_form": budget_form,
                "event": event,
            },
        )


class EventAddMembersView(LoginRequiredMixin, View):

    def post(self, request, pk, user_id):
        event = get_object_or_404(Event, pk=pk)

        if user_id == request.user.id:
            return redirect("events:event-detail", pk=pk)

        EventInvitationService.create_event_invitation(
            list_of_connects=[user_id],
            event_id=event.id
        )

        return redirect("events:event-detail", pk=pk)


class EventAcceptInviteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        EventInvitationService.accept_event_invitation(
            event_id=pk,
            user_id=request.user.id
        )

        return redirect("events:event-detail", pk=pk)


class EventRejectMembersView(LoginRequiredMixin, View):

    def post(self, request, pk, user_id, stay):
        event = get_object_or_404(Event, pk=pk)

        if user_id == request.user.id:
            return redirect("events:event-detail", pk=pk)

        EventInvitationService.reject_event_invitation(
            event_id=event.id,
            user_id=user_id
        )

        if stay == "inside":
            return redirect("events:event-detail", pk=pk)
        else:
            return redirect("events:event-hero")


class EventUpdateMembersView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id):
        event = get_object_or_404(Event, pk=pk)

        if user_id == request.user.id:
            return redirect("events:event-detail", pk=pk)

        EventInvitationService.promote_member(
            event_id=event.id,
            user_id=user_id
        )

        return redirect("events:event-detail", pk=pk)


class EventLeaveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        user = request.user
        EventInvitationService.leave_event(
            event=event,
            user=user
        )
        return redirect("events:event-hero")
