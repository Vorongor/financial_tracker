from django.contrib import admin
from django.urls import path, include

from config import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/", include("accounts.urls")),
    path("", include("dashboard.urls"), name="dashboard"),
    path("events/", include("events.urls"), name="events"),
    path("finances/", include("finances.urls"), name="finances"),
    path("groups/", include("groups.urls"), name="groups"),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
