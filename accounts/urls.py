from django.urls import path

from accounts.views import (
    RegisterView,
    ProfileView,
    UpdateProfileView,
    CommunityListView,
    UserConnectView,
    UserConnectApproveView,
    UserConnectRejectView,
    UserUkConnectView,
)

urlpatterns = [

    path(
        "register/",
        RegisterView.as_view(),
        name="register"
    ),
    path(
        "profile_page/<int:pk>/",
        ProfileView.as_view(),
        name="profile-page"
    ),
    path(
        "profile_page/<int:pk>/update/",
        UpdateProfileView.as_view(),
        name="profile-update"
    ),
    path(
        "community/",
        CommunityListView.as_view(),
        name="community-list"),
    path(
        "connect/<int:user_id>/",
        UserConnectView.as_view(),
        name="user-connect"
    ),
    path(
        "aprove-connect/<int:connection_id>/",
        UserConnectApproveView.as_view(),
        name="approve-connect"
    ),
    path(
        "reject-connect/<int:connection_id>/",
        UserConnectRejectView.as_view(),
        name="reject-connect"
    ),
    path(
        "uk-invite/<str:invite_type>/<int:sender_id>/",
        UserUkConnectView.as_view(),
        name="user-invite-uk"
    )

]
