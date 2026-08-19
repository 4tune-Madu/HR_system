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

    return render(
        request,
        "dashboard.html",
    )