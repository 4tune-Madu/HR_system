from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import (
    AttendanceDeviceEmployee,
    AttendanceRecord,
    AttendanceEvent,
    AttendanceSyncLog,
)


class AttendanceDeviceUserSerializer(serializers.Serializer):
    uid = serializers.IntegerField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True, allow_blank=True)
    privilege = serializers.IntegerField(read_only=True)
    card = serializers.CharField(read_only=True)
    mapped = serializers.BooleanField(read_only=True)
    employee_id = serializers.UUIDField(read_only=True, allow_null=True)
    employee_number = serializers.CharField(read_only=True, allow_null=True)
    employee_name = serializers.CharField(read_only=True, allow_null=True)


class AttendanceDeviceMappingSerializer(serializers.ModelSerializer):
    device = serializers.UUIDField(source="device.id", read_only=True)
    employee = serializers.UUIDField(source="employee.id", read_only=True)
    employee_number = serializers.CharField(
        source="employee.employee_number",
        read_only=True,
    )
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceDeviceEmployee
        fields = [
            "id",
            "device",
            "employee",
            "employee_number",
            "employee_name",
            "device_user_id",
            "display_name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "device",
            "employee",
            "employee_number",
            "employee_name",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(str)
    def get_employee_name(self, obj):
        identity = getattr(obj.employee, "identity", None)

        if identity is None:
            return None

        return " ".join(
            part
            for part in [
                identity.first_name,
                identity.middle_name,
                identity.last_name,
            ]
            if part
        )


class AttendanceDeviceMappingCreateSerializer(serializers.Serializer):
    device_user_id = serializers.CharField(max_length=100)
    employee_id = serializers.UUIDField()
    display_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200,
    )


class AttendanceDeviceMappingUpdateSerializer(serializers.Serializer):
    employee_id = serializers.UUIDField()
    display_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200,
    )


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_id = serializers.UUIDField(
        source="employee.id",
        read_only=True,
    )

    employee_number = serializers.CharField(
        source="employee.employee_number",
        read_only=True,
    )

    employee_name = serializers.SerializerMethodField()

    organization_id = serializers.UUIDField(
        source="organization.id",
        read_only=True,
    )

    class Meta:
        model = AttendanceRecord
        fields = [
            "id",
            "organization_id",
            "employee_id",
            "employee_number",
            "employee_name",
            "attendance_date",
            "status",
            "first_check_in_at",
            "last_check_out_at",
            "checkout_source",
            "worked_minutes",
            "late_minutes",
            "early_departure_minutes",
            "notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "organization_id",
            "employee_id",
            "employee_number",
            "employee_name",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(str)
    def get_employee_name(self, obj):
        identity = getattr(obj.employee, "identity", None)

        if identity is None:
            return None

        return " ".join(
            part
            for part in [
                identity.first_name,
                identity.middle_name,
                identity.last_name,
            ]
            if part
        )

class AttendanceEventSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(
        source="organization.id",
        read_only=True,
    )

    employee_id = serializers.UUIDField(
        source="employee.id",
        read_only=True,
        allow_null=True,
    )

    employee_number = serializers.CharField(
        source="employee.employee_number",
        read_only=True,
        allow_null=True,
    )

    employee_name = serializers.SerializerMethodField()

    device_id = serializers.UUIDField(
        source="device.id",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = AttendanceEvent
        fields = [
            "id",
            "organization_id",
            "employee_id",
            "employee_number",
            "employee_name",
            "device_id",
            "device_user_id",
            "source",
            "event_type",
            "occurred_at",
            "received_at",
            "event_hash",
            "raw_payload",
            "processing_status",
            "processing_error",
            "processed_at",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "organization_id",
            "employee_id",
            "employee_number",
            "employee_name",
            "device_id",
            "received_at",
            "event_hash",
            "processed_at",
            "created_at",
        ]

    @extend_schema_field(str)
    def get_employee_name(self, obj):
        employee = getattr(obj, "employee", None)

        if employee is None:
            return None

        identity = getattr(employee, "identity", None)

        if identity is None:
            return None

        return " ".join(
            part
            for part in [
                identity.first_name,
                identity.middle_name,
                identity.last_name,
            ]
            if part
        )

class ManualAttendanceCheckInSerializer(serializers.Serializer):
    employee_id = serializers.UUIDField()
    occurred_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )

class AttendanceSyncLogSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(
        source="organization.id",
        read_only=True,
    )

    device_id = serializers.UUIDField(
        source="device.id",
        read_only=True,
        allow_null=True,
    )

    device_name = serializers.CharField(
        source="device.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = AttendanceSyncLog
        fields = [
            "id",
            "organization_id",
            "device_id",
            "device_name",
            "trigger",
            "status",
            "start_date",
            "end_date",
            "started_at",
            "completed_at",
            "records_read",
            "records_in_range",
            "created",
            "duplicates",
            "resolved_existing",
            "unresolved",
            "invalid",
            "attendance_days_rebuilt",
            "error_message",
            "updated_at",
        ]
        read_only_fields = fields

class AttendanceDeviceSyncSerializer(serializers.Serializer):
    start_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    end_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if (
            start_date is not None
            and end_date is not None
            and end_date < start_date
        ):
            raise serializers.ValidationError(
                "end_date cannot be earlier than start_date."
            )

        return attrs