from typing import Any

from accounts.services.receive_connection import UserConnectionsService  # noqa
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    TemplateView,
    CreateView,
    DetailView,
    DeleteView,
)

from addition_info.choise_models import Status, Role
from events.forms import EventPrivateCreateForm, EventEditForm
from events.models import Event, EventMembership
from events.services.event_datail_service import EventDetailContextService
from events.services.event_invitation import EventInvitationService
from finances.forms import BudgetEditForm
from finances.models import Budget


class EventHeroView(LoginRequiredMixin, TemplateView):
    template_name = "events/events_list.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
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

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        event = self.object

        service_context = EventDetailContextService.build_context(
            event=event,
            user=self.request.user,
        )

        context.update(service_context)
        return context


class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = Event
    success_url = reverse_lazy("events:event-hero")

    def delete(self, request, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()

        ct = ContentType.objects.get_for_model(self.object)
        Budget.objects.get(owner_type=ct, owner_id=self.object.id).delete()

        return super().delete(request, *args, **kwargs)


class EventUpdateView(LoginRequiredMixin, View):
    template_name = "events/event_edit.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
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
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
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


class BaseEventMemberActionView(LoginRequiredMixin, View):

    def get_event(self, pk: int) -> Event:
        return get_object_or_404(Event, pk=pk)

    def prevent_self_action(
            self,
            request: HttpRequest,
            user_id: int,
            pk: int
    ) -> HttpResponse | None:
        if user_id == request.user.id:
            return redirect("events:event-detail", pk=pk)
        return None

    def success_redirect(self, stay: str, pk: int) -> HttpResponse:
        if stay == "inside":
            return redirect("events:event-detail", pk=pk)
        return redirect("events:event-hero")

    def perform_action(
            self,
            event: Event,
            user_id: int,
            request: HttpRequest
    ) -> None:
        raise NotImplementedError

    def post(
            self,
            request: HttpRequest,
            pk: int,
            user_id: int = None,
            stay: str = None
    ) -> HttpResponse:
        event = self.get_event(pk)

        if user_id is not None:
            stop = self.prevent_self_action(request, user_id, pk)
            if stop:
                return stop

        self.perform_action(event, user_id, request)

        if stay:
            return self.success_redirect(stay, pk)

        return redirect("events:event-detail", pk=pk)


class EventAddMembersView(BaseEventMemberActionView):
    def perform_action(self, event, user_id, request):
        EventInvitationService.create_event_invitation(
            list_of_connects=[user_id],
            event_id=event.id,
        )


class EventAcceptInviteView(BaseEventMemberActionView):
    def perform_action(self, event, user_id, request):
        EventInvitationService.accept_event_invitation(
            event_id=event.id,
            user_id=request.user.id,
        )


class EventRejectMembersView(BaseEventMemberActionView):
    def perform_action(self, event, user_id, request):
        EventInvitationService.reject_event_invitation(
            event_id=event.id,
            user_id=user_id,
        )


class EventUpdateMembersView(BaseEventMemberActionView):
    def perform_action(self, event, user_id, request):
        EventInvitationService.promote_member(
            event_id=event.id,
            user_id=user_id,
        )


class EventLeaveView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        user = request.user
        EventInvitationService.leave_event(
            event=event,
            user=user
        )
        return redirect("events:event-hero")
