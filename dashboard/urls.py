from django.urls import path

from dashboard.views import (
    HomeDashboard,
    PersonalDashView,
    PersonalDashStatsView
)

urlpatterns = [
    path("", HomeDashboard.as_view(), name="dashboard"),

    path(
        "personal/dash/",
        PersonalDashView.as_view(),
        name="personal-dash"
    ),
    path(
        "personal/dash/stats/", PersonalDashStatsView.as_view(),
        name="personal-dash-stats"
    ),

]

app_name = "dashboard"
