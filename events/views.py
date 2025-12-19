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
from accounts.services.receive_connection import get_user_connections
from addition_info.choise_models import Status, Role
from events.forms import EventPrivateCreateForm, EventEditForm
from events.models import Event, EventMembership
from events.services.event_invitation import (
    create_event_invitation,
    reject_event_invitation,
    accept_event_invitation,
    promote_member,
    leave_event
)
from finances.forms import TransferCreateForm, BudgetEditForm
from finances.models import Budget
from groups.models import Group, GroupEventConnection


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
        create_event_invitation(
            list_of_connects=participants_ids,
            event_id=self.object.id
        )

        return redirect(self.get_success_url())


class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        user = self.request.user
        members = EventMembership.objects.filter(event_id=self.object.id)
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
        user_role = members.filter(user=user).first().role
        context["can_delete_event"] = (
                (event.creator and event.creator == user)
                or
                (not event.creator and user_role == "Admin")
        )
        context["transaction_history"] = self.object.budget.transactions.all()
        context["current_budget"] = self.object.budget.get_budget_data()
        context["transaction_form"] = TransferCreateForm()
        context["content_type"] = "event"
        context["object_id"] = event.id
        context["user_role"] = user_role
        if self.object.type == Event.Accessibility.PRIVATE:
            context["connects"] = []
            context["members"] = []

        else:
            context["connects"] = users
            context["members"] = members

        return context


class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = Event
    success_url = reverse_lazy("events:event-hero")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        ct = ContentType.objects.get_for_model(self.object)
        Budget.objects.get(
            owner_type=ct,
            owner_id=self.object.id
        ).delete()

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
            }
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
            return redirect("events:event-detail", pk=pk)

        return render(request, self.template_name, {
            "event_form": event_form,
            "budget_form": budget_form,
            "event": event,
        })


class EventAddMembersView(LoginRequiredMixin, View):

    def post(self, request, pk, user_id):
        event = get_object_or_404(Event, pk=pk)

        if user_id == request.user.id:
            return redirect("events:event-detail", pk=pk)

        create_event_invitation(list_of_connects=[user_id], event_id=event.id)

        return redirect("events:event-detail", pk=pk)


class EventAcceptInviteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        accept_event_invitation(event_id=pk, user_id=request.user.id)

        return redirect("events:event-detail", pk=pk)


class EventRejectMembersView(LoginRequiredMixin, View):

    def post(self, request, pk, user_id, stay):
        event = get_object_or_404(Event, pk=pk)

        if user_id == request.user.id:
            return redirect("events:event-detail", pk=pk)

        reject_event_invitation(event_id=event.id, user_id=user_id)

        if stay == "inside":
            return redirect("events:event-detail", pk=pk)
        else:
            return redirect("events:event-hero")


class EventUpdateMembersView(LoginRequiredMixin, View):
    def post(self, request, pk, user_id):
        event = get_object_or_404(Event, pk=pk)

        if user_id == request.user.id:
            return redirect("events:event-detail", pk=pk)

        promote_member(event_id=event.id, user_id=user_id)

        return redirect("events:event-detail", pk=pk)


class EventLeaveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        user = request.user
        leave_event(event=event, user=user)
        return redirect("events:event-hero")
