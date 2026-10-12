from rest_framework.generics import RetrieveUpdateAPIView

from apps.access.permissions import (
    CanManageAttendanceSettings,
)

from apps.organization.models import Organization
from apps.organization.serializers import (
    OrganizationAttendanceSettingsSerializer,
)


class OrganizationAttendanceSettingsView(
    RetrieveUpdateAPIView
):
    """
    View and update organization-level
    attendance settings.
    """

    serializer_class = (
        OrganizationAttendanceSettingsSerializer
    )

    permission_classes = [
        CanManageAttendanceSettings,
    ]

    def get_queryset(self):
        return Organization.objects.filter(
            is_active=True,
        )

    def get_object(self):
        organization = self.get_queryset().get(
            id=self.kwargs["organization_id"],
        )

        return organization