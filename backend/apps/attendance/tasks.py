from celery import shared_task

from apps.attendance.models import (
    AttendanceDevice,
    AttendanceSyncLog,
    AttendanceRecord,
)
from apps.attendance.services import (
    AttendanceSyncService,
    AttendanceRecordService,
)


@shared_task
def synchronize_attendance_devices():
    """
    Synchronize all active network attendance devices.

    This task is triggered by Celery Beat according to the
    attendance synchronization schedule configured in settings.

    Each device is synchronized independently so that a failure
    on one device does not prevent other devices from syncing.
    """

    devices = (
        AttendanceDevice.objects
        .filter(
            is_active=True,
            connection_type=(
                AttendanceDevice
                .ConnectionType
                .NETWORK
            ),
        )
        .select_related(
            "organization",
        )
        .order_by(
            "organization_id",
            "name",
        )
    )

    summary = {
        "devices_found": devices.count(),
        "devices_succeeded": 0,
        "devices_partial": 0,
        "devices_failed": 0,
        "records_read": 0,
        "records_in_range": 0,
        "created": 0,
        "duplicates": 0,
        "resolved_existing": 0,
        "unresolved": 0,
        "invalid": 0,
        "attendance_days_rebuilt": 0,
    }

    for device in devices:

        try:

            sync_log = (
                AttendanceSyncService.run_sync(
                    device=device,
                    trigger=(
                        AttendanceSyncLog
                        .Trigger
                        .SCHEDULED
                    ),
                )
            )

        except Exception:
            summary["devices_failed"] += 1
            continue

        if (
            sync_log.status
            == AttendanceSyncLog.Status.SUCCESS
        ):
            summary["devices_succeeded"] += 1

        elif (
            sync_log.status
            == AttendanceSyncLog.Status.PARTIAL
        ):
            summary["devices_partial"] += 1

        elif (
            sync_log.status
            == AttendanceSyncLog.Status.FAILED
        ):
            summary["devices_failed"] += 1

        summary["records_read"] += (
            sync_log.records_read
        )

        summary["records_in_range"] += (
            sync_log.records_in_range
        )

        summary["created"] += (
            sync_log.created
        )

        summary["duplicates"] += (
            sync_log.duplicates
        )

        summary["resolved_existing"] += (
            sync_log.resolved_existing
        )

        summary["unresolved"] += (
            sync_log.unresolved
        )

        summary["invalid"] += (
            sync_log.invalid
        )

        summary["attendance_days_rebuilt"] += (
            sync_log.attendance_days_rebuilt
        )

    return summary



@shared_task
def reconcile_open_attendance_records():
    """
    Reconcile open attendance records for organizations that have
    automatic attendance checkout enabled.

    The task intentionally searches historical records as well as
    today's records. This allows the system to recover attendance
    records that remained open because the server was unavailable
    when the normal reconciliation time was reached.

    Example:

        Friday:
            Employee checks in.
            Server is offline at 11:00 PM.
            Attendance record remains open.

        Monday:
            Server starts again.
            This task finds Friday's open record and reconciles it
            using Friday 23:00 as the system checkout time.
    """

    records = (
        AttendanceRecord.objects
        .filter(
            organization__automatic_attendance_checkout_enabled=True,
            first_check_in_at__isnull=False,
            last_check_out_at__isnull=True,
        )
        .select_related(
            "organization",
            "employee",
        )
        .order_by(
            "attendance_date",
            "organization_id",
            "employee_id",
        )
    )

    summary = {
        "records_found": records.count(),
        "records_reconciled": 0,
        "records_skipped": 0,
        "records_failed": 0,
    }

    for record in records:
        try:
            reconciled_record = (
                AttendanceRecordService
                .reconcile_open_attendance_record(
                    record=record,
                )
            )

            if reconciled_record is not None:
                summary["records_reconciled"] += 1
            else:
                summary["records_skipped"] += 1

        except Exception as exc:
            print(
                "ATTENDANCE RECONCILIATION ERROR:",
                repr(exc),
            )

            summary["records_failed"] += 1
            continue
        
    return summary

