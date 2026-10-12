import hashlib
from collections import defaultdict

from django.db import transaction
from django.utils import timezone

from pyzk2 import ZK

from apps.employee.models import Employee

from ..models import (
    AttendanceDevice,
    AttendanceDeviceEmployee,
    AttendanceEvent,
    AttendanceException,
)
from ..services import (
    AttendanceEventService,
    AttendanceRecordService,
)


class FA210Adapter:

    DEFAULT_PORT = 4370
    DEFAULT_TIMEOUT = 10

    # Explicit ZK/Granding punch states that we currently
    # map into our generic attendance event types.
    EXPLICIT_PUNCH_MAP = {
        0: AttendanceEvent.EventType.CHECK_IN,
        1: AttendanceEvent.EventType.CHECK_OUT,
    }

    def __init__(
        self,
        *,
        device,
        timeout=DEFAULT_TIMEOUT,
    ):
        self.device = device
        self.timeout = timeout
        self.connection = None

    # -----------------------------------
    # Connection
    # -----------------------------------

    def connect(self):
        if self.connection is not None:
            return self.connection

        if not self.device.is_active:
            raise ValueError(
                "Attendance device is inactive."
            )

        if not self.device.ip_address:
            raise ValueError(
                "Attendance device does not have "
                "an IP address configured."
            )

        port = (
            self.device.port
            or self.DEFAULT_PORT
        )

        zk = ZK(
            str(self.device.ip_address),
            port=port,
            timeout=self.timeout,
            password=0,
            force_udp=False,
            ommit_ping=False,
        )

        self.connection = zk.connect()

        self.device.last_seen_at = timezone.now()

        self.device.save(
            update_fields=[
                "last_seen_at",
                "updated_at",
            ]
        )

        return self.connection

    def disconnect(self):
        if self.connection is None:
            return

        try:
            self.connection.disconnect()
        finally:
            self.connection = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.disconnect()

    # -----------------------------------
    # Device information
    # -----------------------------------

    def get_device_info(self):

        self.connect()

        return {
            "name": self.connection.get_device_name(),
            "serial_number": (
                self.connection
                .get_serialnumber()
            ),
            "firmware": (
                self.connection
                .get_firmware_version()
            ),
            "platform": (
                self.connection
                .get_platform()
            ),
        }

    # -----------------------------------
    # Device users
    # -----------------------------------

    def get_users(self):

        self.connect()

        return self.connection.get_users()

    # -----------------------------------
    # Attendance logs
    # -----------------------------------

    def get_attendance(self):

        self.connect()

        return self.connection.get_attendance()

    # -----------------------------------
    # Timestamp normalization
    # -----------------------------------

    @staticmethod
    def normalize_timestamp(
        timestamp,
    ):
        if timezone.is_naive(timestamp):
            return timezone.make_aware(
                timestamp,
                timezone.get_current_timezone(),
            )

        return timestamp

    # -----------------------------------
    # Event hash
    # -----------------------------------

    def build_event_hash(
        self,
        *,
        uid,
        user_id,
        timestamp,
        status,
        punch,
    ):
        timestamp = (
            self.normalize_timestamp(
                timestamp
            )
        )

        raw = (
            f"FA210|"
            f"{self.device.id}|"
            f"{uid}|"
            f"{user_id}|"
            f"{timestamp.isoformat()}|"
            f"{status}|"
            f"{punch}"
        )

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

    # -----------------------------------
    # Punch interpretation
    # -----------------------------------

    @classmethod
    def _explicit_event_type(
        cls,
        punch,
    ):
        return cls.EXPLICIT_PUNCH_MAP.get(
            punch
        )

    @classmethod
    def normalize_attendance_records(
        cls,
        records,
    ):
        """
        Convert raw FA210/ZK attendance objects
        into normalized records.

        Explicit punch states are respected.

        When punch == 255 (undefined), we use
        deterministic first-in / next-out sequencing
        for that employee and date.
        """

        grouped = defaultdict(list)

        for record in records:

            user_id = str(
                record.user_id
            )

            timestamp = (
                cls.normalize_timestamp(
                    record.timestamp
                )
            )

            grouped[
                (
                    user_id,
                    timestamp.date(),
                )
            ].append(
                record
            )

        normalized = []

        for (
            user_id,
            attendance_date,
        ), group in grouped.items():

            group.sort(
                key=lambda record: (
                    record.timestamp,
                    getattr(
                        record,
                        "uid",
                        0,
                    ),
                )
            )

            next_undefined_event = (
                AttendanceEvent
                .EventType
                .CHECK_IN
            )

            for record in group:

                timestamp = (
                    cls.normalize_timestamp(
                        record.timestamp
                    )
                )

                uid = getattr(
                    record,
                    "uid",
                    None,
                )

                status = getattr(
                    record,
                    "status",
                    None,
                )

                punch = getattr(
                    record,
                    "punch",
                    None,
                )

                explicit_type = (
                    cls._explicit_event_type(
                        punch
                    )
                )

                inferred = False

                if explicit_type is not None:

                    event_type = (
                        explicit_type
                    )

                    if (
                        event_type
                        == AttendanceEvent
                        .EventType
                        .CHECK_IN
                    ):
                        next_undefined_event = (
                            AttendanceEvent
                            .EventType
                            .CHECK_OUT
                        )

                    else:
                        next_undefined_event = (
                            AttendanceEvent
                            .EventType
                            .CHECK_IN
                        )

                elif punch == 255:

                    event_type = (
                        next_undefined_event
                    )

                    inferred = True

                    if (
                        next_undefined_event
                        == AttendanceEvent
                        .EventType
                        .CHECK_IN
                    ):
                        next_undefined_event = (
                            AttendanceEvent
                            .EventType
                            .CHECK_OUT
                        )
                    else:
                        next_undefined_event = (
                            AttendanceEvent
                            .EventType
                            .CHECK_IN
                        )

                else:

                    event_type = (
                        AttendanceEvent
                        .EventType
                        .UNKNOWN
                    )

                normalized.append(
                    {
                        "uid": uid,
                        "user_id": user_id,
                        "timestamp": timestamp,
                        "status": status,
                        "punch": punch,
                        "event_type": event_type,
                        "inferred_event_type": inferred,
                        "attendance_date": (
                            attendance_date
                        ),
                    }
                )

        normalized.sort(
            key=lambda item: (
                item["timestamp"],
                item["user_id"],
            )
        )

        return normalized

    # -----------------------------------
    # Raw payload
    # -----------------------------------

    @staticmethod
    def build_raw_payload(
        normalized_record,
    ):
        return {
            "uid": normalized_record[
                "uid"
            ],
            "user_id": normalized_record[
                "user_id"
            ],
            "timestamp": (
                normalized_record[
                    "timestamp"
                ].isoformat()
            ),
            "status": normalized_record[
                "status"
            ],
            "punch": normalized_record[
                "punch"
            ],
            "inferred_event_type": (
                normalized_record[
                    "inferred_event_type"
                ]
            ),
        }

    # -----------------------------------
    # Employee mapping
    # -----------------------------------

    def resolve_employee(
        self,
        *,
        user_id,
    ):
        return (
            AttendanceDeviceEmployee.objects
            .select_related(
                "employee",
            )
            .filter(
                device=self.device,
                device_user_id=str(user_id),
                is_active=True,
            )
            .first()
        )

    # -----------------------------------
    # Synchronization
    # -----------------------------------

    @transaction.atomic
    def _create_unknown_employee_exception(
        self,
        *,
        event,
    ):
        existing = (
            AttendanceException.objects
            .filter(
                attendance_event=event,
                exception_type=(
                    AttendanceException
                    .ExceptionType
                    .UNKNOWN_EMPLOYEE
                ),
                status=(
                    AttendanceException
                    .Status
                    .OPEN
                ),
            )
            .exists()
        )

        if existing:
            return

        AttendanceException.objects.create(
            organization=event.organization,
            attendance_event=event,
            exception_type=(
                AttendanceException
                .ExceptionType
                .UNKNOWN_EMPLOYEE
            ),
            description=(
                "FA210 attendance event could not "
                "be mapped to an employee. "
                f"Device User ID: "
                f"{event.device_user_id}"
            ),
        )

    def sync_attendance(
        self,
        start_date=None,
        end_date=None,
    ):

        summary = {
            "records_read": 0,
            "created": 0,
            "duplicates": 0,
            "resolved_existing": 0,
            "unresolved": 0,
            "invalid": 0,
            "attendance_days_rebuilt": 0,
        }

        new_event_ids_by_day = defaultdict(list)

        try:

            self.connect()

            records = self.get_attendance()

            summary[
                "records_read"
            ] = len(records)

            normalized_records = (
                self.normalize_attendance_records(
                    records
                )
            )
            if start_date is not None:
                normalized_records = [
                    item
                    for item in normalized_records
                    if (
                        item["attendance_date"]
                        >= start_date
                    )
                ]

            if end_date is not None:
                normalized_records = [
                    item
                    for item in normalized_records
                    if (
                        item["attendance_date"]
                        <= end_date
                    )
                ]            

            summary[
                "records_in_range"
            ] = len(normalized_records)
            
            for normalized in normalized_records:

                event_hash = (
                    self.build_event_hash(
                        uid=normalized["uid"],
                        user_id=normalized["user_id"],
                        timestamp=normalized["timestamp"],
                        status=normalized["status"],
                        punch=normalized["punch"],
                    )
                )

                existing = (
                    AttendanceEvent.objects
                    .select_related(
                        "employee",
                    )
                    .filter(
                        event_hash=event_hash,
                    )
                    .first()
                )

                # -----------------------------------
                # Existing event
                # -----------------------------------

                if existing is not None:

                    summary[
                        "duplicates"
                    ] += 1

                    # The event may previously have been
                    # unresolved. Try the mapping again.
                    if existing.employee_id is None:

                        mapping = (
                            self.resolve_employee(
                                user_id=(
                                    normalized[
                                        "user_id"
                                    ]
                                ),
                            )
                        )

                        if mapping is not None:

                            existing.employee = (
                                mapping.employee
                            )

                            existing.processing_status = (
                                AttendanceEvent
                                .ProcessingStatus
                                .PENDING
                            )

                            existing.processing_error = ""

                            existing.save(
                                update_fields=[
                                    "employee",
                                    "processing_status",
                                    "processing_error",
                                ]
                            )

                            summary[
                                "resolved_existing"
                            ] += 1

                            if (
                                existing.event_type
                                != AttendanceEvent
                                .EventType
                                .UNKNOWN
                            ):

                                new_event_ids_by_day[
                                    (
                                        existing.employee_id,
                                        normalized[
                                            "attendance_date"
                                        ],
                                    )
                                ].append(
                                    existing.id
                                )

                            else:
                            
                                summary[
                                    "invalid"
                                ] += 1

                                AttendanceEventService.process_event(
                                    event=existing,
                                )

                    continue

                # -----------------------------------
                # New event
                # -----------------------------------

                event = (
                    AttendanceEventService
                    .ingest_event(
                        organization=(
                            self.device
                            .organization
                        ),
                        device=self.device,
                        device_user_id=(
                            normalized[
                                "user_id"
                            ]
                        ),
                        source=(
                            AttendanceEvent
                            .Source
                            .DEVICE
                        ),
                        event_type=(
                            normalized[
                                "event_type"
                            ]
                        ),
                        occurred_at=(
                            normalized[
                                "timestamp"
                            ]
                        ),
                        raw_payload=(
                            self.build_raw_payload(
                                normalized
                            )
                        ),
                        event_hash=event_hash,
                    )
                )

                # Another synchronization process may
                # have inserted it concurrently.

                if event.employee_id is None:

                    self._create_unknown_employee_exception(
                        event=event,
                    )
                
                    summary[
                        "unresolved"
                    ] += 1
                
                    continue
                                
                if (
                    event.event_type
                    == AttendanceEvent
                    .EventType
                    .UNKNOWN
                ):

                    summary[
                        "invalid"
                    ] += 1

                    AttendanceEventService.process_event(
                        event=event
                    )

                    continue

                summary[
                    "created"
                ] += 1

                new_event_ids_by_day[
                    (
                        event.employee_id,
                        normalized[
                            "attendance_date"
                        ],
                    )
                ].append(
                    event.id
                )

            # -----------------------------------
            # Rebuild affected daily records
            # -----------------------------------

            for (
                employee_id,
                attendance_date,
            ), event_ids in (
                new_event_ids_by_day.items()
            ):

                employee = (
                    Employee.objects.get(
                        id=employee_id
                    )
                )

                AttendanceRecordService.rebuild_daily_record(
                    employee=employee,
                    attendance_date=attendance_date,
                )

                (
                    AttendanceEvent.objects
                    .filter(
                        id__in=event_ids,
                    )
                    .update(
                        processing_status=(
                            AttendanceEvent
                            .ProcessingStatus
                            .PROCESSED
                        ),
                        processed_at=timezone.now(),
                        processing_error="",
                    )
                )

                summary[
                    "attendance_days_rebuilt"
                ] += 1

            self.device.last_sync_at = (
                timezone.now()
            )

            self.device.save(
                update_fields=[
                    "last_sync_at",
                    "updated_at",
                ]
            )

            return summary

        finally:
            self.disconnect()