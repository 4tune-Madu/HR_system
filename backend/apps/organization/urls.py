from django.urls import path

from apps.organization.views import (
    OrganizationAttendanceSettingsView,
)


urlpatterns = [
    path(
        "<uuid:organization_id>/attendance/settings/",
        OrganizationAttendanceSettingsView.as_view(),
        name="organization-attendance-settings",
    ),
]