from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


urlpatterns = [

    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "",
        include("apps.core.urls"),
    ),

    path(
        "api/employees/",
        include("apps.employee.urls"),
    ),

    path(
        "api/auth/",
        include("apps.authentication.urls"),
    ),

    path(
        "auth/",
        include("apps.authentication.web_urls"),
    ),

    # API documentation

    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),

    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema"
        ),
        name="swagger-ui",
    ),

    # Web URLs

    path(
        "employees/",
        include(
            "apps.employee.web_urls"
        ),
    ),
]
