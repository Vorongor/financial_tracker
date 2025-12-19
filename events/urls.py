from django.urls import path

from events.views import (
    EventHeroView,
    EventCreateView,
    EventDetailView,
    EventDeleteView,
    EventAddMembersView,
    EventAcceptInviteView,
    EventRejectMembersView,
    EventUpdateMembersView,
    EventLeaveView,
    EventUpdateView,
)

urlpatterns = [
    path(
        "",
        EventHeroView.as_view(),
        name="event-hero"
    ),
    path(
        "create/",
        EventCreateView.as_view(),
        name="private-event-create"
    ),
    path(
        "<int:pk>/",
        EventDetailView.as_view(),
        name="event-detail"
    ),
    path(
        "<int:pk>/update/",
        EventUpdateView.as_view(),
        name="event-update"
    ),
    path(
        "<int:pk>/delete/",
        EventDeleteView.as_view(),
        name="event-delete"
    ),
    path(
        "<int:pk>/members/add/<int:user_id>/",
        EventAddMembersView.as_view(),
        name="event-add-members"
    ),
    path(
        "<int:pk>/accept-invite/",
        EventAcceptInviteView.as_view(),
        name="event-accept-members"
    ),
    path(
        "<int:pk>/reject-members/<int:user_id>/<str:stay>/",
        EventRejectMembersView.as_view(),
        name="event-reject-members"
    ),
    path(
        "<int:pk>/update-members/<int:user_id>/",
        EventUpdateMembersView.as_view(),
        name="event-promote-members"
    ),
    path(
        "<int:pk>/leave-event/",
        EventLeaveView.as_view(),
        name="event-leave"
    ),
]

app_name = "events"
