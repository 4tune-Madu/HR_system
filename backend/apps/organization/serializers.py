from rest_framework import serializers

from apps.organization.models import (
    Branch,
    Department,
    JobGrade,
    Organization,
    Position,
    Team,
)


class OrganizationAttendanceSettingsSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Organization

        fields = [
            "automatic_attendance_checkout_enabled",
        ]


class OrganizationStructureSerializerMixin:
    """Shared organization-scoped structure representation."""


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "organization", "name", "code", "address", "is_active"]
        read_only_fields = ["id", "organization"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "organization", "name", "code", "description", "is_active"]
        read_only_fields = ["id", "organization"]


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "department", "name", "code", "description", "is_active"]
        read_only_fields = ["id"]


class JobGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobGrade
        fields = ["id", "organization", "name", "code", "description", "level", "is_active"]
        read_only_fields = ["id", "organization"]


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ["id", "organization", "department", "job_grade", "title", "code", "description", "is_active"]
        read_only_fields = ["id", "organization"]
