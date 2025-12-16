from django.urls import path

from groups.views import (
    GroupsHomeView,
    GroupCreateView,
    GroupDetailView,
    GroupDeleteView,
    GroupInviteMemberView,
    GroupAcceptInviteView,
    GroupRejectInviteView,
)

urlpatterns = [
    path("", GroupsHomeView.as_view(), name="groups-home"),
    path("create-group/", GroupCreateView.as_view(), name="create-group"),
    path("group-detail/<int:pk>/", GroupDetailView.as_view(),
         name="group-detail"),
    path("group/delete/<int:pk>/", GroupDeleteView.as_view(),
         name="group-delete"),
    path("group/<int:pk>/invite-member/<int:user_id>/",
         GroupInviteMemberView.as_view(), name="group-invite-member"),
    path("group/<int:pk>/accept-invite/<int:user_id>/",
         GroupAcceptInviteView.as_view(), name="group-accept-invite"),
    path("group/<int:pk>/reject-invite/<int:user_id>/<str:stay>/",
         GroupRejectInviteView.as_view(), name="group-reject-invite"),
]
