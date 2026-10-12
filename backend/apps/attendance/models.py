import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.employee.models import Employee
from apps.organization.models import Organization


class AttendanceDevice(models.Model):

    class ConnectionType(models.TextChoices):
        NETWORK = "NETWORK", "Network"
        ADMS = "ADMS", "ADMS"
        USB = "USB", "USB"
        FILE = "FILE", "File"
        API = "API", "API"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="attendance_devices",
    )

    name = models.CharField(
        max_length=150,
    )

    vendor = models.CharField(
        max_length=100,
        blank=True,
    )

    model = models.CharField(
        max_length=100,
        blank=True,
    )

    serial_number = models.CharField(
        max_length=150,
        blank=True,
    )

    mac_address = models.CharField(
        max_length=100,
        blank=True,
    )

    connection_type = models.CharField(
        max_length=20,
        choices=ConnectionType.choices,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    port = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
        ],
    )

    is_active = models.BooleanField(
        default=True,
    )

    last_seen_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    configuration = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "serial_number",
                ],
                condition=~models.Q(
                    serial_number=""
                ),
                name=(
                    "unique_attendance_device_serial_per_organization"
                ),
            ),
        ]

    def __str__(self):
        return self.name


class AttendanceDeviceEmployee(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    device = models.ForeignKey(
        AttendanceDevice,
        on_delete=models.CASCADE,
        related_name="employee_mappings",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="attendance_device_mappings",
    )

    device_user_id = models.CharField(
        max_length=100,
    )

    display_name = models.CharField(
        max_length=200,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "device",
                    "device_user_id",
                ],
                name=(
                    "unique_device_user_id_per_attendance_device"
                ),
            ),
            models.UniqueConstraint(
                fields=[
                    "device",
                    "employee",
                ],
                name=(
                    "unique_employee_mapping_per_attendance_device"
                ),
            ),
        ]

    def __str__(self):
        return (
            f"{self.device} - "
            f"{self.employee} - "
            f"{self.device_user_id}"
        )


class AttendanceEvent(models.Model):

    class Source(models.TextChoices):
        DEVICE = "DEVICE", "Device"
        WEB = "WEB", "Web"
        MOBILE = "MOBILE", "Mobile"
        API = "API", "API"
        IMPORT = "IMPORT", "Import"
        MANUAL = "MANUAL", "Manual"
        SYSTEM = "SYSTEM", "System"

    class EventType(models.TextChoices):
        CHECK_IN = "CHECK_IN", "Check In"
        CHECK_OUT = "CHECK_OUT", "Check Out"
        UNKNOWN = "UNKNOWN", "Unknown"

    class ProcessingStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSED = "PROCESSED", "Processed"
        FAILED = "FAILED", "Failed"
        IGNORED = "IGNORED", "Ignored"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="attendance_events",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_events",
    )

    device = models.ForeignKey(
        AttendanceDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_events",
    )

    device_user_id = models.CharField(
        max_length=100,
        blank=True,
    )

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
    )

    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.UNKNOWN,
    )

    occurred_at = models.DateTimeField()

    received_at = models.DateTimeField(
        auto_now_add=True,
    )

    event_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        unique=True,
    )

    raw_payload = models.JSONField(
        default=dict,
        blank=True,
    )

    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )

    processing_error = models.TextField(
        blank=True,
    )

    processed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-occurred_at",
        ]

    def __str__(self):
        return (
            f"{self.device_user_id or self.employee_id} - "
            f"{self.event_type} - "
            f"{self.occurred_at}"
        )


class AttendanceRecord(models.Model):

    class CheckoutSource(models.TextChoices):
        NONE = "NONE", "None"
        DEVICE = "DEVICE", "Device"
        WEB = "WEB", "Web"
        MOBILE = "MOBILE", "Mobile"
        API = "API", "API"
        MANUAL = "MANUAL", "Manual"
        SYSTEM = "SYSTEM", "System"

    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        INCOMPLETE = "INCOMPLETE", "Incomplete"
        OFF_DAY = "OFF_DAY", "Off Day"
        HOLIDAY = "HOLIDAY", "Holiday"
        ON_LEAVE = "ON_LEAVE", "On Leave"
        EXCUSED = "EXCUSED", "Excused"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    attendance_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
    )

    first_check_in_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_check_out_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    checkout_source = models.CharField(
        max_length=20,
        choices=CheckoutSource.choices,
        default=CheckoutSource.NONE,
    )

    worked_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    late_minutes = models.PositiveIntegerField(
        default=0,
    )

    early_departure_minutes = models.PositiveIntegerField(
        default=0,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-attendance_date",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "employee",
                    "attendance_date",
                ],
                name=(
                    "unique_employee_attendance_record_per_day"
                ),
            ),
        ]

    def __str__(self):
        return (
            f"{self.employee} - "
            f"{self.attendance_date}"
        )


class AttendanceException(models.Model):

    class ExceptionType(models.TextChoices):
        UNKNOWN_EMPLOYEE = (
            "UNKNOWN_EMPLOYEE",
            "Unknown Employee",
        )
        DUPLICATE_EVENT = (
            "DUPLICATE_EVENT",
            "Duplicate Event",
        )
        MISSING_CHECK_IN = (
            "MISSING_CHECK_IN",
            "Missing Check In",
        )
        MISSING_CHECK_OUT = (
            "MISSING_CHECK_OUT",
            "Missing Check Out",
        )
        INVALID_EVENT = (
            "INVALID_EVENT",
            "Invalid Event",
        )
        DEVICE_ERROR = (
            "DEVICE_ERROR",
            "Device Error",
        )
        MANUAL_REVIEW = (
            "MANUAL_REVIEW",
            "Manual Review",
        )

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        RESOLVED = "RESOLVED", "Resolved"
        DISMISSED = "DISMISSED", "Dismissed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="attendance_exceptions",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_exceptions",
    )

    attendance_record = models.ForeignKey(
        AttendanceRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exceptions",
    )

    attendance_event = models.ForeignKey(
        AttendanceEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exceptions",
    )

    exception_type = models.CharField(
        max_length=30,
        choices=ExceptionType.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )

    description = models.TextField()

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_attendance_exceptions",
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    resolution_note = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return (
            f"{self.exception_type} - "
            f"{self.employee_id or 'Unknown'}"
        )


class AttendanceSyncLog(models.Model):

    class Status(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        PARTIAL = "PARTIAL", "Partial"
        FAILED = "FAILED", "Failed"

    class Trigger(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        SCHEDULED = "SCHEDULED", "Scheduled"
        API = "API", "API"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="attendance_sync_logs",
    )

    device = models.ForeignKey(
        AttendanceDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sync_logs",
    )

    trigger = models.CharField(
        max_length=20,
        choices=Trigger.choices,
        default=Trigger.MANUAL,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RUNNING,
    )

    start_date = models.DateField(
        null=True,
        blank=True,
    )

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    records_read = models.PositiveIntegerField(
        default=0,
    )

    records_in_range = models.PositiveIntegerField(
        default=0,
    )

    created = models.PositiveIntegerField(
        default=0,
    )

    duplicates = models.PositiveIntegerField(
        default=0,
    )

    resolved_existing = models.PositiveIntegerField(
        default=0,
    )

    unresolved = models.PositiveIntegerField(
        default=0,
    )

    invalid = models.PositiveIntegerField(
        default=0,
    )

    attendance_days_rebuilt = models.PositiveIntegerField(
        default=0,
    )

    error_message = models.TextField(
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-started_at",
        ]

    def __str__(self):
        return (
            f"{self.device or 'Unknown Device'} - "
            f"{self.status} - "
            f"{self.started_at}"
        )