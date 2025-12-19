from django.urls import path

from groups.views import (
    GroupsHomeView,
    GroupCreateView,
    GroupDetailView,
    GroupDeleteView,
    GroupInviteMemberView,
    GroupAcceptInviteView,
    GroupRejectInviteView,
    GroupPromoteView,
    GroupDemoteView,
    LeaveGroupView,
    GroupEditView,
    GroupEventsCreateView,
)

urlpatterns = [
    path("", GroupsHomeView.as_view(), name="home"),
    path("create-group/", GroupCreateView.as_view(), name="create"),
    path("detail/<int:pk>/", GroupDetailView.as_view(), name="detail"),
    path("update/<int:pk>/", GroupEditView.as_view(), name="update"),
    path("delete/<int:pk>/", GroupDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/invite-member/<int:user_id>/",
        GroupInviteMemberView.as_view(),
        name="invite-member",
    ),
    path(
        "<int:pk>/accept-invite/<int:user_id>/",
        GroupAcceptInviteView.as_view(),
        name="accept-invite",
    ),
    path(
        "<int:pk>/reject-invite/<int:user_id>/<str:stay>/",
        GroupRejectInviteView.as_view(),
        name="reject-invite",
    ),
    path("<int:pk>/promote/<int:user_id>/", GroupPromoteView.as_view(), name="promote"),
    path("<int:pk>/demote/<int:user_id>/", GroupDemoteView.as_view(), name="demote"),
    path("leave-group/<int:group_id>/", LeaveGroupView.as_view(), name="leave-group"),
    path(
        "<int:group_id>/create-event//",
        GroupEventsCreateView.as_view(),
        name="create-inside-event",
    ),
]

app_name = "groups"
