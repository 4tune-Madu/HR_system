import hashlib
import json

from django.db import transaction, models
from django.utils import timezone
from datetime import datetime, time, timedelta
from .models import (
    AttendanceDevice,
    AttendanceDeviceEmployee,
    AttendanceEvent,
    AttendanceRecord,
    AttendanceException,
    AttendanceSyncLog,
)

from apps.leave.models import (
    LeaveRequest,
    PublicHoliday,
    EmployeeWorkSchedule,
    WorkScheduleDay,
)


class AttendanceSyncService:

    @staticmethod
    @transaction.atomic
    def start_sync(
        *,
        organization,
        device,
        start_date=None,
        end_date=None,
        trigger=AttendanceSyncLog.Trigger.MANUAL,
    ):
        if (
            device.organization_id
            != organization.id
        ):
            raise ValueError(
                "Attendance device does not belong "
                "to this organization."
            )

        return AttendanceSyncLog.objects.create(
            organization=organization,
            device=device,
            trigger=trigger,
            status=(
                AttendanceSyncLog
                .Status
                .RUNNING
            ),
            start_date=start_date,
            end_date=end_date,
        )

    @staticmethod
    @transaction.atomic
    def complete_sync(
        *,
        sync_log,
        summary,
    ):
        if sync_log.status != (
            AttendanceSyncLog
            .Status
            .RUNNING
        ):
            raise ValueError(
                "Only a running synchronization "
                "can be completed."
            )

        sync_log.records_read = summary.get(
            "records_read",
            0,
        )

        sync_log.records_in_range = summary.get(
            "records_in_range",
            0,
        )

        sync_log.created = summary.get(
            "created",
            0,
        )

        sync_log.duplicates = summary.get(
            "duplicates",
            0,
        )

        sync_log.resolved_existing = summary.get(
            "resolved_existing",
            0,
        )

        sync_log.unresolved = summary.get(
            "unresolved",
            0,
        )

        sync_log.invalid = summary.get(
            "invalid",
            0,
        )

        sync_log.attendance_days_rebuilt = (
            summary.get(
                "attendance_days_rebuilt",
                0,
            )
        )

        has_processing_issues = (
            sync_log.unresolved > 0
            or sync_log.invalid > 0
        )

        sync_log.status = (
            AttendanceSyncLog
            .Status
            .PARTIAL
            if has_processing_issues
            else (
                AttendanceSyncLog
                .Status
                .SUCCESS
            )
        )

        sync_log.completed_at = timezone.now()

        sync_log.save(
            update_fields=[
                "records_read",
                "records_in_range",
                "created",
                "duplicates",
                "resolved_existing",
                "unresolved",
                "invalid",
                "attendance_days_rebuilt",
                "status",
                "completed_at",
                "updated_at",
            ]
        )

        return sync_log

    @staticmethod
    @transaction.atomic
    def fail_sync(
        *,
        sync_log,
        error_message,
        summary=None,
    ):
        if sync_log.status != (
            AttendanceSyncLog
            .Status
            .RUNNING
        ):
            raise ValueError(
                "Only a running synchronization "
                "can be failed."
            )

        summary = (
            summary
            if summary is not None
            else {}
        )

        sync_log.records_read = summary.get(
            "records_read",
            0,
        )

        sync_log.records_in_range = summary.get(
            "records_in_range",
            0,
        )

        sync_log.created = summary.get(
            "created",
            0,
        )

        sync_log.duplicates = summary.get(
            "duplicates",
            0,
        )

        sync_log.resolved_existing = summary.get(
            "resolved_existing",
            0,
        )

        sync_log.unresolved = summary.get(
            "unresolved",
            0,
        )

        sync_log.invalid = summary.get(
            "invalid",
            0,
        )

        sync_log.attendance_days_rebuilt = (
            summary.get(
                "attendance_days_rebuilt",
                0,
            )
        )

        sync_log.status = (
            AttendanceSyncLog
            .Status
            .FAILED
        )

        sync_log.error_message = str(
            error_message
        )

        sync_log.completed_at = timezone.now()

        sync_log.save(
            update_fields=[
                "records_read",
                "records_in_range",
                "created",
                "duplicates",
                "resolved_existing",
                "unresolved",
                "invalid",
                "attendance_days_rebuilt",
                "status",
                "error_message",
                "completed_at",
                "updated_at",
            ]
        )

        return sync_log

    @staticmethod
    def get_sync_logs(
        *,
        organization,
        device=None,
    ):
        queryset = (
            AttendanceSyncLog.objects
            .filter(
                organization=organization,
            )
            .select_related(
                "device",
            )
        )

        if device is not None:
            queryset = queryset.filter(
                device=device,
            )

        return queryset


    @staticmethod
    def run_sync(
        *,
        device,
        start_date=None,
        end_date=None,
        trigger=AttendanceSyncLog.Trigger.MANUAL,
    ):
        sync_log = (
            AttendanceSyncService.start_sync(
                organization=device.organization,
                device=device,
                start_date=start_date,
                end_date=end_date,
                trigger=trigger,
            )
        )

        summary = {}

        try:

            from .integrations.fa210 import (
                FA210Adapter,
            )

            adapter = FA210Adapter(
                device=device,
            )

            summary = adapter.sync_attendance(
                start_date=start_date,
                end_date=end_date,
            )

        except Exception as exc:

            AttendanceSyncService.fail_sync(
                sync_log=sync_log,
                error_message=str(exc),
                summary=summary,
            )

            raise

        AttendanceSyncService.complete_sync(
            sync_log=sync_log,
            summary=summary,
        )

        sync_log.refresh_from_db()

        return sync_log

class AttendanceDeviceService:

    @staticmethod
    def get_device(
        *,
        device_id,
        organization,
    ):
        return AttendanceDevice.objects.get(
            id=device_id,
            organization=organization,
        )

    @staticmethod
    @transaction.atomic
    def register_device(
        *,
        organization,
        name,
        vendor="",
        model="",
        serial_number="",
        mac_address="",
        connection_type=AttendanceDevice.ConnectionType.NETWORK,
        ip_address=None,
        port=None,
        configuration=None,
    ):
        if serial_number:
            duplicate = (
                AttendanceDevice.objects
                .filter(
                    organization=organization,
                    serial_number=serial_number,
                )
                .exists()
            )

            if duplicate:
                raise ValueError(
                    "An attendance device with this "
                    "serial number already exists "
                    "in this organization."
                )

        return AttendanceDevice.objects.create(
            organization=organization,
            name=name,
            vendor=vendor,
            model=model,
            serial_number=serial_number,
            mac_address=mac_address,
            connection_type=connection_type,
            ip_address=ip_address,
            port=port,
            configuration=(
                configuration
                if configuration is not None
                else {}
            ),
        )

    @staticmethod
    @transaction.atomic
    def update_device(
        *,
        device,
        organization,
        name,
        vendor="",
        model="",
        serial_number="",
        mac_address="",
        connection_type=AttendanceDevice.ConnectionType.NETWORK,
        ip_address=None,
        port=None,
        configuration=None,
    ):
        if (
            device.organization_id
            != organization.id
        ):
            raise ValueError(
                "Attendance device does not belong "
                "to this organization."
            )

        if serial_number:

            duplicate = (
                AttendanceDevice.objects
                .filter(
                    organization=organization,
                    serial_number=serial_number,
                )
                .exclude(
                    id=device.id,
                )
                .exists()
            )

            if duplicate:
                raise ValueError(
                    "Another attendance device with this "
                    "serial number already exists "
                    "in this organization."
                )

        device.name = name
        device.vendor = vendor
        device.model = model
        device.serial_number = serial_number
        device.mac_address = mac_address
        device.connection_type = connection_type
        device.ip_address = ip_address
        device.port = port

        if configuration is not None:
            device.configuration = configuration

        device.save(
            update_fields=[
                "name",
                "vendor",
                "model",
                "serial_number",
                "mac_address",
                "connection_type",
                "ip_address",
                "port",
                "configuration",
                "updated_at",
            ]
        )

        return device

    @staticmethod
    @transaction.atomic
    def deactivate_device(
        *,
        device,
        organization,
    ):
        if (
            device.organization_id
            != organization.id
        ):
            raise ValueError(
                "Attendance device does not belong "
                "to this organization."
            )

        if not device.is_active:
            raise ValueError(
                "Attendance device is already inactive."
            )

        device.is_active = False

        device.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return device

    @staticmethod
    @transaction.atomic
    def activate_device(
        *,
        device,
        organization,
    ):
        if (
            device.organization_id
            != organization.id
        ):
            raise ValueError(
                "Attendance device does not belong "
                "to this organization."
            )

        if device.is_active:
            raise ValueError(
                "Attendance device is already active."
            )

        device.is_active = True

        device.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return device

    @staticmethod
    @transaction.atomic
    def map_employee(
        *,
        device,
        employee,
        device_user_id,
        display_name="",
    ):
        if (
            device.organization_id
            != employee.organization_id
        ):
            raise ValueError(
                "Attendance device and employee "
                "must belong to the same organization."
            )

        if not employee.is_active:
            raise ValueError(
                "An inactive employee cannot be "
                "mapped to an attendance device."
            )

        if not device.is_active:
            raise ValueError(
                "An inactive attendance device "
                "cannot receive employee mappings."
            )

        device_user_id = str(
            device_user_id or ""
        ).strip()

        if not device_user_id:
            raise ValueError(
                "Device user ID is required."
            )

        mapping = (
            AttendanceDeviceEmployee.objects
            .select_for_update()
            .filter(
                device=device,
                device_user_id=device_user_id,
            )
            .first()
        )

        if mapping:

            if mapping.employee_id != employee.id:
                raise ValueError(
                    "This device user ID is already "
                    "mapped to another employee. "
                    "Use remap_employee() to change it."
                )

            mapping.display_name = (
                display_name
                or mapping.display_name
            )
            mapping.is_active = True

            mapping.save(
                update_fields=[
                    "display_name",
                    "is_active",
                    "updated_at",
                ]
            )

            return mapping

        existing_employee = (
            AttendanceDeviceEmployee.objects
            .filter(
                device=device,
                employee=employee,
            )
            .first()
        )

        if existing_employee:
            if existing_employee.is_active:
                raise ValueError(
                    "This employee is already mapped "
                    "to this attendance device."
                )

            existing_employee.device_user_id = (
                device_user_id
            )
            existing_employee.display_name = (
                display_name
            )
            existing_employee.is_active = True

            existing_employee.save(
                update_fields=[
                    "device_user_id",
                    "display_name",
                    "is_active",
                    "updated_at",
                ]
            )

            return existing_employee

        return AttendanceDeviceEmployee.objects.create(
            device=device,
            employee=employee,
            device_user_id=device_user_id,
            display_name=display_name,
        )


    @staticmethod
    @transaction.atomic
    def remap_employee(
        *,
        device,
        device_user_id,
        employee,
        display_name="",
    ):
        if (
            device.organization_id
            != employee.organization_id
        ):
            raise ValueError(
                "Attendance device and employee "
                "must belong to the same organization."
            )

        if not employee.is_active:
            raise ValueError(
                "An inactive employee cannot be "
                "mapped to an attendance device."
            )

        if not device.is_active:
            raise ValueError(
                "An inactive attendance device "
                "cannot receive employee mappings."
            )

        device_user_id = str(
            device_user_id or ""
        ).strip()

        if not device_user_id:
            raise ValueError(
                "Device user ID is required."
            )

        mapping = (
            AttendanceDeviceEmployee.objects
            .select_for_update()
            .filter(
                device=device,
                device_user_id=device_user_id,
            )
            .first()
        )

        if mapping is None:
            raise ValueError(
                "No mapping exists for this device user ID."
            )

        if mapping.employee_id == employee.id:
            mapping.display_name = (
                display_name
                or mapping.display_name
            )
            mapping.is_active = True

            mapping.save(
                update_fields=[
                    "display_name",
                    "is_active",
                    "updated_at",
                ]
            )

            return mapping

        employee_mapping = (
            AttendanceDeviceEmployee.objects
            .filter(
                device=device,
                employee=employee,
            )
            .exclude(
                id=mapping.id,
            )
            .first()
        )

        if employee_mapping:
            raise ValueError(
                "This employee is already mapped "
                "to this attendance device."
            )

        mapping.employee = employee
        mapping.display_name = display_name
        mapping.is_active = True

        mapping.save(
            update_fields=[
                "employee",
                "display_name",
                "is_active",
                "updated_at",
            ]
        )

        return mapping


    @staticmethod
    @transaction.atomic
    def unmap_employee(
        *,
        device,
        device_user_id,
    ):
        device_user_id = str(
            device_user_id or ""
        ).strip()

        if not device_user_id:
            raise ValueError(
                "Device user ID is required."
            )

        mapping = (
            AttendanceDeviceEmployee.objects
            .select_for_update()
            .filter(
                device=device,
                device_user_id=device_user_id,
                is_active=True,
            )
            .first()
        )

        if mapping is None:
            raise ValueError(
                "No active employee mapping exists "
                "for this device user ID."
            )

        mapping.is_active = False

        mapping.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return mapping

    @staticmethod
    def get_mapping(
        *,
        device,
        device_user_id,
    ):
        return (
            AttendanceDeviceEmployee.objects
            .select_related(
                "employee",
                "employee__identity",
            )
            .filter(
                device=device,
                device_user_id=str(
                    device_user_id
                ).strip(),
            )
            .first()
        )

    @staticmethod
    def get_all_employee_mappings(
        *,
        device,
    ):
        return (
            AttendanceDeviceEmployee.objects
            .filter(
                device=device,
            )
            .select_related(
                "employee",
                "employee__identity",
            )
            .order_by(
                "device_user_id",
            )
        )


    @staticmethod
    def get_device_users(
        *,
        device,
    ):
        """
        Retrieve users currently registered on the
        physical attendance device.

        This does not create or alter employee mappings.
        """

        if not device.is_active:
            raise ValueError(
                "Attendance device is inactive."
            )

        if not device.ip_address:
            raise ValueError(
                "Attendance device does not have "
                "an IP address configured."
            )

        from .integrations.fa210 import (
            FA210Adapter,
        )

        adapter = FA210Adapter(
            device=device,
        )

        try:
            return adapter.get_users()
        finally:
            adapter.disconnect()

    @staticmethod
    def get_employee_mappings(
        *,
        device,
    ):
        return (
            AttendanceDeviceEmployee.objects
            .filter(
                device=device,
                is_active=True,
            )
            .select_related(
                "employee",
                "employee__identity",
            )
            .order_by(
                "device_user_id",
            )
        )


class AttendanceEventService:

    @staticmethod
    def _generate_event_hash(
        *,
        organization,
        device,
        device_user_id,
        source,
        event_type,
        occurred_at,
        raw_payload,
    ):
        payload = {
            "organization_id": str(
                organization.id
            ),
            "device_id": (
                str(device.id)
                if device
                else None
            ),
            "device_user_id": str(
                device_user_id or ""
            ),
            "source": source,
            "event_type": event_type,
            "occurred_at": occurred_at.isoformat(),
            "raw_payload": raw_payload or {},
        }

        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
            default=str,
        ).encode(
            "utf-8"
        )

        return hashlib.sha256(
            encoded
        ).hexdigest()

    @staticmethod
    def resolve_employee(
        *,
        device,
        device_user_id,
    ):
        if device is None:
            return None

        if not device_user_id:
            return None

        mapping = (
            AttendanceDeviceEmployee.objects
            .select_related(
                "employee",
            )
            .filter(
                device=device,
                device_user_id=str(
                    device_user_id
                ),
                is_active=True,
            )
            .first()
        )

        if mapping is None:
            return None

        return mapping.employee

    @classmethod
    @transaction.atomic
    def ingest_event(
        cls,
        *,
        organization,
        occurred_at,
        source,
        event_type=AttendanceEvent.EventType.UNKNOWN,
        device=None,
        device_user_id="",
        employee=None,
        raw_payload=None,
        event_hash=None,
    ):
        raw_payload = (
            raw_payload
            if raw_payload is not None
            else {}
        )

        if device is not None:

            if (
                device.organization_id
                != organization.id
            ):
                raise ValueError(
                    "Attendance device does not belong "
                    "to this organization."
                )

            if not device.is_active:
                raise ValueError(
                    "Attendance device is inactive."
                )

        if employee is not None:

            if (
                employee.organization_id
                != organization.id
            ):
                raise ValueError(
                    "Employee does not belong "
                    "to this organization."
                )

        if employee is None and device is not None:
            employee = cls.resolve_employee(
                device=device,
                device_user_id=device_user_id,
            )

        if event_hash is None:
            event_hash = cls._generate_event_hash(
                organization=organization,
                device=device,
                device_user_id=device_user_id,
                source=source,
                event_type=event_type,
                occurred_at=occurred_at,
                raw_payload=raw_payload,
            )

        existing = (
            AttendanceEvent.objects
            .filter(
                event_hash=event_hash,
            )
            .first()
        )

        if existing:
            if (
                existing.organization_id
                != organization.id
            ):
                raise ValueError(
                    "Attendance event hash already "
                    "belongs to another organization."
                )

            return existing

        return AttendanceEvent.objects.create(
            organization=organization,
            employee=employee,
            device=device,
            device_user_id=str(
                device_user_id or ""
            ),
            source=source,
            event_type=event_type,
            occurred_at=occurred_at,
            event_hash=event_hash,
            raw_payload=raw_payload,
        )

    @staticmethod
    @transaction.atomic
    def process_event(
        *,
        event,
    ):
        event = (
            AttendanceEvent.objects
            .select_for_update()
            .select_related(
                "employee",
                "device",
            )
            .get(
                id=event.id,
            )
        )

        if (
            event.processing_status
            == AttendanceEvent
            .ProcessingStatus.PROCESSED
        ):
            return event

        if event.employee is None:

            exception_exists = (
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
                        .Status.OPEN
                    ),
                )
                .exists()
            )

            if not exception_exists:
                AttendanceException.objects.create(
                    organization=event.organization,
                    attendance_event=event,
                    exception_type=(
                        AttendanceException
                        .ExceptionType
                        .UNKNOWN_EMPLOYEE
                    ),
                    description=(
                        "Attendance event could not be "
                        "matched to an employee."
                    ),
                )

            event.processing_status = (
                AttendanceEvent
                .ProcessingStatus.FAILED
            )

            event.processing_error = (
                "No employee mapping exists "
                "for this attendance event."
            )

            event.save(
                update_fields=[
                    "processing_status",
                    "processing_error",
                ]
            )

            return event

        if (
            event.event_type
            == AttendanceEvent.EventType.UNKNOWN
        ):
            exception_exists = (
                AttendanceException.objects
                .filter(
                    attendance_event=event,
                    exception_type=(
                        AttendanceException
                        .ExceptionType
                        .INVALID_EVENT
                    ),
                    status=(
                        AttendanceException
                        .Status.OPEN
                    ),
                )
                .exists()
            )

            if not exception_exists:
                AttendanceException.objects.create(
                    organization=event.organization,
                    employee=event.employee,
                    attendance_event=event,
                    exception_type=(
                        AttendanceException
                        .ExceptionType
                        .INVALID_EVENT
                    ),
                    description=(
                        "Attendance event has an "
                        "unknown event type."
                    ),
                )

            event.processing_status = (
                AttendanceEvent
                .ProcessingStatus.FAILED
            )

            event.processing_error = (
                "Attendance event type is unknown."
            )

            event.save(
                update_fields=[
                    "processing_status",
                    "processing_error",
                ]
            )

            return event

        AttendanceRecordService.rebuild_daily_record(
            employee=event.employee,
            attendance_date=(
                event.occurred_at.date()
            ),
        )

        event.processing_status = (
            AttendanceEvent
            .ProcessingStatus.PROCESSED
        )

        event.processed_at = timezone.now()
        event.processing_error = ""

        event.save(
            update_fields=[
                "processing_status",
                "processed_at",
                "processing_error",
            ]
        )

        return event

    @classmethod
    @transaction.atomic
    def manual_check_in(
        cls,
        *,
        organization,
        employee,
        occurred_at=None,
        raw_payload=None,
    ):
        if (
            employee.organization_id
            != organization.id
        ):
            raise ValueError(
                "Employee does not belong "
                "to this organization."
            )
    
        if not employee.is_active:
            raise ValueError(
                "An inactive employee cannot "
                "be checked in."
            )
    
        occurred_at = (
            occurred_at
            if occurred_at is not None
            else timezone.now()
        )
    
        event = cls.ingest_event(
            organization=organization,
            employee=employee,
            occurred_at=occurred_at,
            source=AttendanceEvent.Source.MANUAL,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            raw_payload=(
                raw_payload
                if raw_payload is not None
                else {
                    "type": "manual_check_in",
                }
            ),
        )
    
        return cls.process_event(
            event=event,
        )
    
class AttendanceRecordService:

    @staticmethod
    @transaction.atomic
    def rebuild_daily_record(
        *,
        employee,
        attendance_date,
    ):
        events = list(
            AttendanceEvent.objects
            .filter(
                employee=employee,
                occurred_at__date=attendance_date,
                processing_status__in=[
                    AttendanceEvent
                    .ProcessingStatus.PENDING,
                    AttendanceEvent
                    .ProcessingStatus.PROCESSED,
                ],
                event_type__in=[
                    AttendanceEvent.EventType.CHECK_IN,
                    AttendanceEvent.EventType.CHECK_OUT,
                ],
            )
            .order_by(
                "occurred_at",
            )
        )

        record, created = (
            AttendanceRecord.objects
            .get_or_create(
                employee=employee,
                attendance_date=attendance_date,
                defaults={
                    "organization": employee.organization,
                },
            )
        )

        if (
            record.organization_id
            != employee.organization_id
        ):
            raise ValueError(
                "Attendance record and employee "
                "belong to different organizations."
            )

        check_ins = [
            event
            for event in events
            if (
                event.event_type
                == AttendanceEvent.EventType.CHECK_IN
            )
        ]

        check_outs = [
            event
            for event in events
            if (
                event.event_type
                == AttendanceEvent.EventType.CHECK_OUT
            )
        ]

        first_check_in = (
            check_ins[0].occurred_at
            if check_ins
            else None
        )

        last_check_out = (
            check_outs[-1].occurred_at
            if check_outs
            else None
        )

        # ----------------------------------------------------
        # Determine checkout source
        # ----------------------------------------------------

        if last_check_out is None:
            checkout_source = (
                AttendanceRecord
                .CheckoutSource
                .NONE
            )

        else:
            last_checkout_event = check_outs[-1]

            source_mapping = {
                AttendanceEvent.Source.DEVICE: (
                    AttendanceRecord
                    .CheckoutSource
                    .DEVICE
                ),
                AttendanceEvent.Source.WEB: (
                    AttendanceRecord
                    .CheckoutSource
                    .WEB
                ),
                AttendanceEvent.Source.MOBILE: (
                    AttendanceRecord
                    .CheckoutSource
                    .MOBILE
                ),
                AttendanceEvent.Source.API: (
                    AttendanceRecord
                    .CheckoutSource
                    .API
                ),
                AttendanceEvent.Source.MANUAL: (
                    AttendanceRecord
                    .CheckoutSource
                    .MANUAL
                ),
                AttendanceEvent.Source.SYSTEM: (
                        AttendanceRecord
                        .CheckoutSource
                        .SYSTEM
                    ),
            }

            checkout_source = source_mapping.get(
                last_checkout_event.source,
                AttendanceRecord
                .CheckoutSource
                .API,
            )

        # ----------------------------------------------------
        # Calculate worked minutes from actual events
        # ----------------------------------------------------

        total_worked_minutes = 0

        current_check_in = None

        for event in events:

            if (
                event.event_type
                == AttendanceEvent.EventType.CHECK_IN
            ):
                if current_check_in is None:
                    current_check_in = (
                        event.occurred_at
                    )

                continue

            if (
                event.event_type
                == AttendanceEvent.EventType.CHECK_OUT
            ):

                if current_check_in is None:
                    continue

                duration = (
                    event.occurred_at
                    - current_check_in
                )

                minutes = int(
                    duration.total_seconds()
                    // 60
                )

                if minutes > 0:
                    total_worked_minutes += minutes

                current_check_in = None

        # ----------------------------------------------------
        # Determine status from attendance events
        # ----------------------------------------------------

        if not events:
            status_value = (
                AttendanceRecord.Status.ABSENT
            )

        elif (
            first_check_in is not None
            and last_check_out is not None
        ):
            status_value = (
                AttendanceRecord.Status.PRESENT
            )

        else:
            status_value = (
                AttendanceRecord.Status.INCOMPLETE
            )

        # ----------------------------------------------------
        # Calculate late arrival and early departure
        # ----------------------------------------------------

        late_minutes = 0
        early_departure_minutes = 0

        employee_work_schedule = (
            EmployeeWorkSchedule.objects
            .select_related(
                "work_schedule",
            )
            .filter(
                employee=employee,
                effective_from__lte=attendance_date,
                is_active=True,
            )
            .filter(
                models.Q(
                    effective_to__isnull=True,
                )
                | models.Q(
                    effective_to__gte=attendance_date,
                )
            )
            .order_by(
                "-effective_from",
            )
            .first()
        )

        if employee_work_schedule:

            work_schedule = (
                employee_work_schedule
                .work_schedule
            )

            schedule_day = (
                WorkScheduleDay.objects
                .filter(
                    work_schedule=work_schedule,
                    day_of_week=(
                        attendance_date.weekday()
                    ),
                )
                .first()
            )

            if schedule_day:

                # ------------------------------------------------
                # Late arrival
                # ------------------------------------------------

                if first_check_in is not None:

                    scheduled_start = (
                        timezone.make_aware(
                            datetime.combine(
                                attendance_date,
                                schedule_day.start_time,
                            )
                        )
                    )

                    grace_end = (
                        scheduled_start
                        + timedelta(
                            minutes=(
                                schedule_day
                                .grace_period_minutes
                            )
                        )
                    )

                    if first_check_in > grace_end:

                        late_minutes = int(
                            (
                                first_check_in
                                - grace_end
                            ).total_seconds()
                            // 60
                        )

                # ------------------------------------------------
                # Early departure
                # ------------------------------------------------

                if last_check_out is not None:

                    # A system-generated 11 PM checkout
                    # is not considered an employee departure.
                    if (
                        checkout_source
                        != (
                            AttendanceRecord
                            .CheckoutSource
                            .SYSTEM
                        )
                    ):

                        scheduled_end = (
                            timezone.make_aware(
                                datetime.combine(
                                    attendance_date,
                                    schedule_day.end_time,
                                )
                            )
                        )

                        if last_check_out < scheduled_end:

                            early_departure_minutes = int(
                                (
                                    scheduled_end
                                    - last_check_out
                                ).total_seconds()
                                // 60
                            )

        # ----------------------------------------------------
        # Save attendance record
        # ----------------------------------------------------

        record.first_check_in_at = first_check_in
        record.last_check_out_at = last_check_out
        record.checkout_source = checkout_source

        record.worked_minutes = (
            total_worked_minutes
            if total_worked_minutes > 0
            else None
        )

        record.late_minutes = late_minutes
        record.early_departure_minutes = (
            early_departure_minutes
        )

        record.status = status_value

        record.save(
            update_fields=[
                "first_check_in_at",
                "last_check_out_at",
                "checkout_source",
                "worked_minutes",
                "late_minutes",
                "early_departure_minutes",
                "status",
                "updated_at",
            ]
        )

        return record


    @staticmethod
    @transaction.atomic
    def reconcile_open_attendance_record(
        *,
        record,
    ):
        """
        Reconcile one open attendance record.#


        An attendance record is eligible for automatic closure when:

        - automatic attendance checkout is enabled
          for the employee's organization
        - the employee has checked in
        - no actual checkout exists
        - the attendance date is not a public holiday
        - the employee is not on approved leave
        - the attendance date is a scheduled workday

        The automatic checkout time is 11:00 PM on the
        attendance date.

        The system checkout is recorded as an AttendanceEvent so
        that AttendanceEvent remains the source of truth for
        rebuilding AttendanceRecord.

        This method is intentionally date-based rather than
        current-time-based so that missed reconciliations can
        recover historical attendance records.
        """

        # ---------------------------------------------------------
        # 1. Organization policy
        # ---------------------------------------------------------

        organization = record.organization

        if not organization.automatic_attendance_checkout_enabled:
            return None

        # ---------------------------------------------------------
        # 2. The employee must have checked in
        # ---------------------------------------------------------

        if record.first_check_in_at is None:
            return None

        # ---------------------------------------------------------
        # 3. Never overwrite an actual checkout
        # ---------------------------------------------------------

        if record.last_check_out_at is not None:
            return None

        # ---------------------------------------------------------
        # 4. Public holiday
        # ---------------------------------------------------------

        if DailyAttendanceService.is_public_holiday(
            employee=record.employee,
            attendance_date=record.attendance_date,
        ):
            return None

        # ---------------------------------------------------------
        # 5. Approved leave
        # ---------------------------------------------------------

        if DailyAttendanceService.is_employee_on_leave(
            employee=record.employee,
            attendance_date=record.attendance_date,
        ):
            return None

        # ---------------------------------------------------------
        # 6. Work schedule
        # ---------------------------------------------------------

        schedule_assignment = (
            DailyAttendanceService
            .get_employee_work_schedule(
                employee=record.employee,
                attendance_date=record.attendance_date,
            )
        )

        if schedule_assignment is None:
            return None

        work_schedule = schedule_assignment.work_schedule

        # ---------------------------------------------------------
        # 7. Scheduled off day
        # ---------------------------------------------------------

        if not DailyAttendanceService.is_scheduled_workday(
            work_schedule=work_schedule,
            attendance_date=record.attendance_date,
        ):
            return None

        # ---------------------------------------------------------
        # 8. Build the 11:00 PM system checkout time
        #    for the ATTENDANCE DATE.
        #
        #    Friday record -> Friday 11 PM
        #    not Monday 11 PM.
        #
        #    This allows historical records to recover correctly
        #    after server downtime.
        # ---------------------------------------------------------

        checkout_time = timezone.make_aware(
            datetime.combine(
                record.attendance_date,
                time(
                    hour=23,
                    minute=0,
                ),
            ),
            timezone.get_current_timezone(),
        )

        # ---------------------------------------------------------
        # 9. Do not create a checkout before the employee checked in
        # ---------------------------------------------------------

        if checkout_time <= record.first_check_in_at:
            return None

        # ---------------------------------------------------------
        # 10. Create the SYSTEM checkout event
        #
        #     AttendanceEvent is the source of truth.
        #     AttendanceRecord will be rebuilt from this event.
        # ---------------------------------------------------------

        existing_system_checkout = (
            AttendanceEvent.objects
            .filter(
                organization=organization,
                employee=record.employee,
                source=AttendanceEvent.Source.SYSTEM,
                event_type=AttendanceEvent.EventType.CHECK_OUT,
                occurred_at=checkout_time,
                processing_status=(
                    AttendanceEvent
                    .ProcessingStatus
                    .PROCESSED
                ),
            )
            .first()
        )

        if existing_system_checkout is None:
            AttendanceEvent.objects.create(
                organization=organization,
                employee=record.employee,
                source=AttendanceEvent.Source.SYSTEM,
                event_type=AttendanceEvent.EventType.CHECK_OUT,
                occurred_at=checkout_time,
                processing_status=(
                    AttendanceEvent
                    .ProcessingStatus
                    .PROCESSED
                ),
                raw_payload={
                    "type": "automatic_attendance_checkout",
                    "attendance_date": str(
                        record.attendance_date
                    ),
                    "checkout_time": checkout_time.isoformat(),
                },
            )

        # ---------------------------------------------------------
        # 11. Rebuild the attendance record from events
        #
        #     This ensures:
        #
        #     AttendanceEvent
        #            ↓
        #     AttendanceRecord
        #
        #     remains the single source of truth.
        # ---------------------------------------------------------

        return AttendanceRecordService.rebuild_daily_record(
            employee=record.employee,
            attendance_date=record.attendance_date,
        )

    @staticmethod
    def get_daily_record(
        *,
        employee,
        attendance_date,
    ):
        return AttendanceRecord.objects.get(
            employee=employee,
            attendance_date=attendance_date,
        )

# ============================================================
# DAILY ATTENDANCE PROCESSING SERVICE
# ============================================================


class DailyAttendanceService:

    @staticmethod
    def get_employee_work_schedule(
        employee,
        attendance_date,
    ):
        """
        Return the work schedule applicable to an employee
        on a specific date.

        An EmployeeWorkSchedule is applicable when:

        - it belongs to the employee
        - it is active
        - effective_from <= attendance_date
        - effective_to is NULL OR
          effective_to >= attendance_date

        The most recent effective assignment is selected.
        """

        return (
            EmployeeWorkSchedule.objects
            .filter(
                employee=employee,
                is_active=True,
                effective_from__lte=attendance_date,
            )
            .filter(
                models.Q(
                    effective_to__isnull=True,
                )
                | models.Q(
                    effective_to__gte=attendance_date,
                )
            )
            .select_related(
                "work_schedule",
            )
            .order_by(
                "-effective_from",
            )
            .first()
        )

    @staticmethod
    def is_public_holiday(
        employee,
        attendance_date,
    ):
        """
        Determine whether the attendance date is an active
        public holiday for the employee's organization.
        """

        return PublicHoliday.objects.filter(
            organization=employee.organization,
            date=attendance_date,
            is_active=True,
        ).exists()

    @staticmethod
    def is_employee_on_leave(
        employee,
        attendance_date,
    ):
        """
        Determine whether the employee has an approved leave
        request covering the attendance date.
        """

        return LeaveRequest.objects.filter(
            organization=employee.organization,
            employee=employee,
            status=LeaveRequest.Status.APPROVED,
            start_date__lte=attendance_date,
            end_date__gte=attendance_date,
        ).exists()

    @staticmethod
    def is_scheduled_workday(
        work_schedule,
        attendance_date,
    ):
        """
        Determine whether the employee's work schedule considers
        the given weekday a working day.
        """

        weekday_fields = {
            0: "monday",
            1: "tuesday",
            2: "wednesday",
            3: "thursday",
            4: "friday",
            5: "saturday",
            6: "sunday",
        }

        field_name = weekday_fields[
            attendance_date.weekday()
        ]

        return getattr(
            work_schedule,
            field_name,
        )

    @staticmethod
    @transaction.atomic
    def process_employee_day(
        employee,
        attendance_date,
    ):
        """
        Process one employee's attendance for one date.

        Processing priority:

        1. Public holiday
        2. Approved leave
        3. Work schedule / off day
        4. Attendance events

        The existing AttendanceRecordService remains responsible
        for calculating event-derived values such as:

        - first_check_in_at
        - last_check_out_at
        - worked_minutes

        This service is responsible for applying the daily
        attendance business status.
        """

        # ----------------------------------------------------
        # 1. Rebuild attendance data from attendance events
        # ----------------------------------------------------

        record = (
            AttendanceRecordService
            .rebuild_daily_record(
                employee=employee,
                attendance_date=attendance_date,
            )
        )

        # ----------------------------------------------------
        # 2. Public holiday
        # ----------------------------------------------------

        if DailyAttendanceService.is_public_holiday(
            employee=employee,
            attendance_date=attendance_date,
        ):
            record.status = AttendanceRecord.Status.HOLIDAY
            record.notes = "Public holiday."

            record.save(
                update_fields=[
                    "status",
                    "notes",
                    "updated_at",
                ]
            )

            return record

        # ----------------------------------------------------
        # 3. Approved leave
        # ----------------------------------------------------

        if DailyAttendanceService.is_employee_on_leave(
            employee=employee,
            attendance_date=attendance_date,
        ):
            record.status = AttendanceRecord.Status.ON_LEAVE
            record.notes = "Employee is on approved leave."

            record.save(
                update_fields=[
                    "status",
                    "notes",
                    "updated_at",
                ]
            )

            return record

        # ----------------------------------------------------
        # 4. Determine applicable work schedule
        # ----------------------------------------------------

        schedule_assignment = (
            DailyAttendanceService
            .get_employee_work_schedule(
                employee=employee,
                attendance_date=attendance_date,
            )
        )

        # ----------------------------------------------------
        # 5. No schedule assignment
        # ----------------------------------------------------

        if schedule_assignment is None:
            record.notes = (
                "No active work schedule assignment "
                "was found for this date."
            )

            record.save(
                update_fields=[
                    "notes",
                    "updated_at",
                ]
            )

            return record

        work_schedule = (
            schedule_assignment.work_schedule
        )

        # ----------------------------------------------------
        # 6. Scheduled off day
        # ----------------------------------------------------

        if not DailyAttendanceService.is_scheduled_workday(
            work_schedule=work_schedule,
            attendance_date=attendance_date,
        ):
            record.status = AttendanceRecord.Status.OFF_DAY
            record.notes = "Scheduled off day."

            record.save(
                update_fields=[
                    "status",
                    "notes",
                    "updated_at",
                ]
            )

            return record

        # ----------------------------------------------------
        # 7. Working day
        # ----------------------------------------------------

        if (
            record.first_check_in_at is not None
            and record.last_check_out_at is not None
        ):
            record.status = (
                AttendanceRecord.Status.PRESENT
            )

        elif (
            record.first_check_in_at is not None
            or record.last_check_out_at is not None
        ):
            record.status = (
                AttendanceRecord.Status.INCOMPLETE
            )

        else:
            record.status = (
                AttendanceRecord.Status.ABSENT
            )

        record.notes = ""

        record.save(
            update_fields=[
                "status",
                "notes",
                "updated_at",
            ]
        )

        return record