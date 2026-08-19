from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    MeView,
)

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)


urlpatterns = [
    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),

    path(
        "refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),

    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),

    path(
        "me/",
        MeView.as_view(),
        name="me",
    ),
]