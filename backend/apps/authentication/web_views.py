from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy


class WebLoginView(LoginView):

    template_name = "authentication/login.html"

    redirect_authenticated_user = True

    next_page = reverse_lazy(
        "dashboard"
    )


class WebLogoutView(LogoutView):
    next_page = reverse_lazy("login")


from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard_view(request):
    is_system_admin = (
        request.user.is_superuser
        or request.user.is_staff
    )

    if is_system_admin:
        return render(
            request,
            "dashboard_system_admin.html",
            {
                "user": request.user,
            },
        )

    return render(
        request,
        "dashboard.html",
        {
            "user": request.user,
        },
    )