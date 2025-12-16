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

)

urlpatterns = [
    path("hero/", EventHeroView.as_view(), name="event-hero"),
    path("create/", EventCreateView.as_view(),
         name="private-event-create"),
    path("event/<int:pk>/", EventDetailView.as_view(), name="event-detail"),
    path("delete/<int:pk>/", EventDeleteView.as_view(), name="event-delete"),
    path("event/<int:pk>/invite-members/<int:user_id>/",
         EventAddMembersView.as_view(),
         name="event-add-members"),
    path("event/<int:pk>/accept-invite/",
         EventAcceptInviteView.as_view(),
         name="event-accept-members"),
    path("event/<int:pk>/reject-members/<int:user_id>/<str:stay>/",
         EventRejectMembersView.as_view(),
         name="event-reject-members"),
    path("event/<int:pk>/update-members/<int:user_id>/",
         EventUpdateMembersView.as_view(),
         name="event-update-members"),

]

app_name = "events"
