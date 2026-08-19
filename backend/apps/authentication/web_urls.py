from django.urls import path

from .web_views import (
    WebLoginView,
    WebLogoutView,
    dashboard_view,
)


urlpatterns = [
    path("login/", WebLoginView.as_view(), name="login"),
    path("logout/", WebLogoutView.as_view(), name="logout"),
    path("dashboard/", dashboard_view, name="dashboard"),
]