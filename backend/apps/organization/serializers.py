from rest_framework import serializers

from apps.organization.models import Organization


class OrganizationAttendanceSettingsSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Organization

        fields = [
            "automatic_attendance_checkout_enabled",
        ]