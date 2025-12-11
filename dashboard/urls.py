from django.urls import path

from dashboard.views import HomeDashboard

urlpatterns = [
    path("", HomeDashboard.as_view(), name="dashboard"),
]

app_name="dashboard"
