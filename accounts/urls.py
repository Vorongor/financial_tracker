from django.urls import path

from accounts.views import RegisterView, ProfileView

urlpatterns = [

    path("register/", RegisterView.as_view(), name="register"),
    path("profile_page/<int:pk>/", ProfileView.as_view(), name="profile-page"),

]
