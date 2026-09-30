from datetime import datetime, timezone as dt_timezone
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from datetime import date, datetime, time, timezone as dt_timezone

from apps.organization.models import Organization
from apps.employee.models import Employee
from apps.employee.services import EmployeeService

from apps.attendance.models import (
    AttendanceDevice,
    AttendanceDeviceEmployee,
    AttendanceEvent,
    AttendanceRecord,
    AttendanceException,
    AttendanceSyncLog,
)

from apps.attendance.services import (
    AttendanceDeviceService,
    AttendanceEventService,
    AttendanceRecordService,
    AttendanceSyncService,
    DailyAttendanceService,
)

from apps.leave.models import (
    LeaveRequest,
    LeaveType,
    PublicHoliday,
    WorkSchedule,
    WorkScheduleDay,
    EmployeeWorkSchedule,
)

from apps.attendance.tasks import (
    reconcile_open_attendance_records,
)

class AttendanceDeviceServiceTests(TestCase):

    def setUp(self):

        self.organization = (
            Organization.objects.create(
                name="Test Company",
                legal_name="Test Company Limited",
            )
        )

        self.employee = (
            EmployeeService.create_employee(
                organization=self.organization,
                first_name="John",
                last_name="Doe",
                company_email="john@testcompany.com",
            )
        )

    def test_register_device(self):

        device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
                vendor="Granding",
                model="FA210-Plus",
                serial_number="FA210-001",
                mac_address="AA:BB:CC:DD:EE:FF",
                connection_type=(
                    AttendanceDevice
                    .ConnectionType.NETWORK
                ),
                ip_address="192.168.1.50",
                port=4370,
            )
        )

        self.assertEqual(
            device.organization,
            self.organization,
        )

        self.assertEqual(
            device.vendor,
            "Granding",
        )

        self.assertEqual(
            device.model,
            "FA210-Plus",
        )

    def test_duplicate_device_serial_is_rejected(self):

        AttendanceDeviceService.register_device(
            organization=self.organization,
            name="Main Entrance",
            serial_number="FA210-001",
        )

        with self.assertRaises(ValueError):

            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Second Device",
                serial_number="FA210-001",
            )

    def test_map_employee_to_device(self):

        device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
            )
        )

        mapping = (
            AttendanceDeviceService.map_employee(
                device=device,
                employee=self.employee,
                device_user_id="105",
                display_name="John Doe",
            )
        )

        self.assertEqual(
            mapping.device,
            device,
        )

        self.assertEqual(
            mapping.employee,
            self.employee,
        )

        self.assertEqual(
            mapping.device_user_id,
            "105",
        )

    def test_same_device_user_id_cannot_map_to_two_employees(
        self,
    ):

        employee_two = (
            EmployeeService.create_employee(
                organization=self.organization,
                first_name="Jane",
                last_name="Doe",
                company_email="jane@testcompany.com",
            )
        )

        device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
            )
        )

        AttendanceDeviceService.map_employee(
            device=device,
            employee=self.employee,
            device_user_id="105",
        )

        with self.assertRaises(ValueError):

            AttendanceDeviceService.map_employee(
                device=device,
                employee=employee_two,
                device_user_id="105",
            )

    def test_remap_employee(
        self,
    ):
        employee_two = (
            EmployeeService.create_employee(
                organization=self.organization,
                first_name="Jane",
                last_name="Doe",
                company_email="jane@testcompany.com",
            )
        )

        device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
            )
        )

        AttendanceDeviceService.map_employee(
            device=device,
            employee=self.employee,
            device_user_id="105",
        )

        mapping = (
            AttendanceDeviceService.remap_employee(
                device=device,
                device_user_id="105",
                employee=employee_two,
            )
        )

        self.assertEqual(
            mapping.employee,
            employee_two,
        )

        self.assertEqual(
            mapping.device_user_id,
            "105",
        )

        self.assertTrue(
            mapping.is_active,
        )

    def test_remap_to_already_mapped_employee_is_rejected(
        self,
    ):
        employee_two = (
            EmployeeService.create_employee(
                organization=self.organization,
                first_name="Jane",
                last_name="Doe",
                company_email="jane@testcompany.com",
            )
        )

        device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
            )
        )

        AttendanceDeviceService.map_employee(
            device=device,
            employee=self.employee,
            device_user_id="105",
        )

        AttendanceDeviceService.map_employee(
            device=device,
            employee=employee_two,
            device_user_id="106",
        )

        with self.assertRaises(ValueError):

            AttendanceDeviceService.remap_employee(
                device=device,
                device_user_id="105",
                employee=employee_two,
            )

    def test_unmap_employee(
        self,
    ):
        device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
            )
        )

        AttendanceDeviceService.map_employee(
            device=device,
            employee=self.employee,
            device_user_id="105",
        )

        mapping = (
            AttendanceDeviceService.unmap_employee(
                device=device,
                device_user_id="105",
            )
        )

        mapping.refresh_from_db()

        self.assertFalse(
            mapping.is_active,
        )


    def test_unmap_inactive_mapping_is_rejected(
        self,
    ):
        device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
            )
        )

        AttendanceDeviceService.map_employee(
            device=device,
            employee=self.employee,
            device_user_id="105",
        )

        AttendanceDeviceService.unmap_employee(
            device=device,
            device_user_id="105",
        )

        with self.assertRaises(ValueError):

            AttendanceDeviceService.unmap_employee(
                device=device,
                device_user_id="105",
            )

    def test_get_mapping(
        self,
    ):
        device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
            )
        )

        AttendanceDeviceService.map_employee(
            device=device,
            employee=self.employee,
            device_user_id="105",
            display_name="John Doe",
        )

        mapping = (
            AttendanceDeviceService.get_mapping(
                device=device,
                device_user_id="105",
            )
        )

        self.assertIsNotNone(
            mapping,
        )

        self.assertEqual(
            mapping.employee,
            self.employee,
        )

        self.assertEqual(
            mapping.display_name,
            "John Doe",
        )

    def test_get_all_employee_mappings(
        self,
    ):
        employee_two = (
            EmployeeService.create_employee(
                organization=self.organization,
                first_name="Jane",
                last_name="Doe",
                company_email="jane@testcompany.com",
            )
        )

        device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
            )
        )

        AttendanceDeviceService.map_employee(
            device=device,
            employee=self.employee,
            device_user_id="105",
        )

        AttendanceDeviceService.map_employee(
            device=device,
            employee=employee_two,
            device_user_id="106",
        )

        mappings = (
            AttendanceDeviceService
            .get_all_employee_mappings(
                device=device,
            )
        )

        self.assertEqual(
            mappings.count(),
            2,
        )

        self.assertEqual(
            list(
                mappings.values_list(
                    "device_user_id",
                    flat=True,
                )
            ),
            [
                "105",
                "106",
            ],
        )


class AttendanceEventServiceTests(TestCase):

    def setUp(self):

        self.organization = (
            Organization.objects.create(
                name="Test Company",
                legal_name="Test Company Limited",
            )
        )

        self.employee = (
            EmployeeService.create_employee(
                organization=self.organization,
                first_name="John",
                last_name="Doe",
                company_email="john@testcompany.com",
            )
        )

        self.device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
                vendor="Granding",
                model="FA210-Plus",
                serial_number="FA210-001",
            )
        )

        AttendanceDeviceService.map_employee(
            device=self.device,
            employee=self.employee,
            device_user_id="105",
        )

    def test_ingest_event_resolves_employee_from_device_mapping(
        self,
    ):

        occurred_at = datetime(
            2026,
            9,
            21,
            8,
            0,
            0,
            tzinfo=dt_timezone.utc,
        )

        event = (
            AttendanceEventService.ingest_event(
                organization=self.organization,
                device=self.device,
                device_user_id="105",
                source=(
                    AttendanceEvent.Source.DEVICE
                ),
                event_type=(
                    AttendanceEvent
                    .EventType
                    .CHECK_IN
                ),
                occurred_at=occurred_at,
                raw_payload={
                    "user_id": "105",
                },
            )
        )

        self.assertEqual(
            event.employee,
            self.employee,
        )

        self.assertEqual(
            event.device_user_id,
            "105",
        )

    def test_duplicate_event_is_idempotent(
        self,
    ):

        occurred_at = datetime(
            2026,
            9,
            21,
            8,
            0,
            0,
            tzinfo=dt_timezone.utc,
        )

        first = (
            AttendanceEventService.ingest_event(
                organization=self.organization,
                device=self.device,
                device_user_id="105",
                source=(
                    AttendanceEvent.Source.DEVICE
                ),
                event_type=(
                    AttendanceEvent
                    .EventType
                    .CHECK_IN
                ),
                occurred_at=occurred_at,
                raw_payload={
                    "user_id": "105",
                },
            )
        )

        second = (
            AttendanceEventService.ingest_event(
                organization=self.organization,
                device=self.device,
                device_user_id="105",
                source=(
                    AttendanceEvent.Source.DEVICE
                ),
                event_type=(
                    AttendanceEvent
                    .EventType
                    .CHECK_IN
                ),
                occurred_at=occurred_at,
                raw_payload={
                    "user_id": "105",
                },
            )
        )

        self.assertEqual(
            first.id,
            second.id,
        )

        self.assertEqual(
            AttendanceEvent.objects.count(),
            1,
        )

    def test_unknown_device_user_creates_unresolved_event(
        self,
    ):

        occurred_at = datetime(
            2026,
            9,
            21,
            8,
            0,
            0,
            tzinfo=dt_timezone.utc,
        )

        event = (
            AttendanceEventService.ingest_event(
                organization=self.organization,
                device=self.device,
                device_user_id="999",
                source=(
                    AttendanceEvent.Source.DEVICE
                ),
                event_type=(
                    AttendanceEvent
                    .EventType
                    .CHECK_IN
                ),
                occurred_at=occurred_at,
                raw_payload={
                    "user_id": "999",
                },
            )
        )

        self.assertIsNone(
            event.employee,
        )

        self.assertEqual(
            event.processing_status,
            AttendanceEvent
            .ProcessingStatus
            .PENDING,
        )

    def test_unknown_employee_event_creates_exception(
        self,
    ):

        occurred_at = datetime(
            2026,
            9,
            21,
            8,
            0,
            0,
            tzinfo=dt_timezone.utc,
        )

        event = (
            AttendanceEventService.ingest_event(
                organization=self.organization,
                device=self.device,
                device_user_id="999",
                source=(
                    AttendanceEvent.Source.DEVICE
                ),
                event_type=(
                    AttendanceEvent
                    .EventType
                    .CHECK_IN
                ),
                occurred_at=occurred_at,
            )
        )

        AttendanceEventService.process_event(
            event=event,
        )

        event.refresh_from_db()

        self.assertEqual(
            event.processing_status,
            AttendanceEvent
            .ProcessingStatus
            .FAILED,
        )

        self.assertTrue(
            AttendanceException.objects.filter(
                attendance_event=event,
                exception_type=(
                    AttendanceException
                    .ExceptionType
                    .UNKNOWN_EMPLOYEE
                ),
            ).exists()
        )


class AttendanceRecordServiceTests(TestCase):

    def setUp(self):

        self.organization = (
            Organization.objects.create(
                name="Test Company",
                legal_name="Test Company Limited",
            )
        )

        self.employee = (
            EmployeeService.create_employee(
                organization=self.organization,
                first_name="John",
                last_name="Doe",
                company_email="john@testcompany.com",
            )
        )

        self.device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
                vendor="Granding",
                model="FA210-Plus",
                serial_number="FA210-001",
            )
        )

        AttendanceDeviceService.map_employee(
            device=self.device,
            employee=self.employee,
            device_user_id="105",
        )

    def test_complete_day_creates_present_record(
        self,
    ):

        check_in = datetime(
            2026,
            9,
            21,
            8,
            0,
            0,
            tzinfo=dt_timezone.utc,
        )

        lunch_out = datetime(
            2026,
            9,
            21,
            12,
            0,
            0,
            tzinfo=dt_timezone.utc,
        )

        lunch_in = datetime(
            2026,
            9,
            21,
            13,
            0,
            0,
            tzinfo=dt_timezone.utc,
        )

        check_out = datetime(
            2026,
            9,
            21,
            17,
            0,
            0,
            tzinfo=dt_timezone.utc,
        )

        for occurred_at, event_type in [
            (
                check_in,
                AttendanceEvent
                .EventType
                .CHECK_IN,
            ),
            (
                lunch_out,
                AttendanceEvent
                .EventType
                .CHECK_OUT,
            ),
            (
                lunch_in,
                AttendanceEvent
                .EventType
                .CHECK_IN,
            ),
            (
                check_out,
                AttendanceEvent
                .EventType
                .CHECK_OUT,
            ),
        ]:

            AttendanceEventService.ingest_event(
                organization=self.organization,
                device=self.device,
                device_user_id="105",
                source=(
                    AttendanceEvent.Source.DEVICE
                ),
                event_type=event_type,
                occurred_at=occurred_at,
            )

        record = (
            AttendanceRecordService
            .rebuild_daily_record(
                employee=self.employee,
                attendance_date=datetime(
                    2026,
                    9,
                    21,
                    tzinfo=dt_timezone.utc,
                ).date(),
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.PRESENT,
        )

        self.assertEqual(
            record.worked_minutes,
            480,
        )

        self.assertEqual(
            record.first_check_in_at,
            check_in,
        )

        self.assertEqual(
            record.last_check_out_at,
            check_out,
        )

    def test_check_in_without_check_out_is_incomplete(
        self,
    ):

        occurred_at = datetime(
            2026,
            9,
            21,
            8,
            0,
            0,
            tzinfo=dt_timezone.utc,
        )

        AttendanceEventService.ingest_event(
            organization=self.organization,
            device=self.device,
            device_user_id="105",
            source=(
                AttendanceEvent.Source.DEVICE
            ),
            event_type=(
                AttendanceEvent.EventType.CHECK_IN
            ),
            occurred_at=occurred_at,
        )

        record = (
            AttendanceRecordService
            .rebuild_daily_record(
                employee=self.employee,
                attendance_date=occurred_at.date(),
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.INCOMPLETE,
        )

        self.assertEqual(
            record.first_check_in_at,
            occurred_at,
        )

        self.assertIsNone(
            record.last_check_out_at,
        )

    def test_multiple_check_in_and_check_out_pairs_are_calculated(
        self,
    ):

        events = [
            (
                datetime(
                    2026,
                    9,
                    21,
                    8,
                    0,
                    tzinfo=dt_timezone.utc,
                ),
                AttendanceEvent
                .EventType
                .CHECK_IN,
            ),
            (
                datetime(
                    2026,
                    9,
                    21,
                    10,
                    0,
                    tzinfo=dt_timezone.utc,
                ),
                AttendanceEvent
                .EventType
                .CHECK_OUT,
            ),
            (
                datetime(
                    2026,
                    9,
                    21,
                    10,
                    30,
                    tzinfo=dt_timezone.utc,
                ),
                AttendanceEvent
                .EventType
                .CHECK_IN,
            ),
            (
                datetime(
                    2026,
                    9,
                    21,
                    17,
                    0,
                    tzinfo=dt_timezone.utc,
                ),
                AttendanceEvent
                .EventType
                .CHECK_OUT,
            ),
        ]

        for occurred_at, event_type in events:

            AttendanceEventService.ingest_event(
                organization=self.organization,
                device=self.device,
                device_user_id="105",
                source=(
                    AttendanceEvent.Source.DEVICE
                ),
                event_type=event_type,
                occurred_at=occurred_at,
            )

        record = (
            AttendanceRecordService
            .rebuild_daily_record(
                employee=self.employee,
                attendance_date=events[0][0].date(),
            )
        )

        self.assertEqual(
            record.worked_minutes,
            510,
        )


class AttendanceSyncServiceTests(
    TestCase
):

    def setUp(self):

        self.organization = (
            Organization.objects.create(
                name="Test Company",
                legal_name="Test Company Limited",
            )
        )

        self.employee = (
            EmployeeService.create_employee(
                organization=self.organization,
                first_name="John",
                last_name="Doe",
                company_email="john@testcompany.com",
            )
        )

        self.device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
                vendor="Granding",
                model="FA210-Plus",
                serial_number="FA210-001",
            )
        )

    def test_start_sync_creates_running_log(
        self,
    ):

        sync_log = (
            AttendanceSyncService.start_sync(
                organization=self.organization,
                device=self.device,
                start_date=(
                    datetime(
                        2026,
                        9,
                        21,
                    ).date()
                ),
                end_date=(
                    datetime(
                        2026,
                        9,
                        21,
                    ).date()
                ),
            )
        )

        self.assertEqual(
            sync_log.organization,
            self.organization,
        )

        self.assertEqual(
            sync_log.device,
            self.device,
        )

        self.assertEqual(
            sync_log.status,
            AttendanceSyncLog.Status.RUNNING,
        )

        self.assertEqual(
            sync_log.trigger,
            AttendanceSyncLog.Trigger.MANUAL,
        )

        self.assertIsNone(
            sync_log.completed_at,
        )

    def test_complete_sync_marks_success(
        self,
    ):

        sync_log = (
            AttendanceSyncService.start_sync(
                organization=self.organization,
                device=self.device,
            )
        )

        result = (
            AttendanceSyncService.complete_sync(
                sync_log=sync_log,
                summary={
                    "records_read": 100,
                    "records_in_range": 20,
                    "created": 20,
                    "duplicates": 0,
                    "resolved_existing": 0,
                    "unresolved": 0,
                    "invalid": 0,
                    "attendance_days_rebuilt": 10,
                },
            )
        )

        self.assertEqual(
            result.status,
            AttendanceSyncLog.Status.SUCCESS,
        )

        self.assertEqual(
            result.records_read,
            100,
        )

        self.assertEqual(
            result.records_in_range,
            20,
        )

        self.assertEqual(
            result.created,
            20,
        )

        self.assertEqual(
            result.attendance_days_rebuilt,
            10,
        )

        self.assertIsNotNone(
            result.completed_at,
        )

    def test_complete_sync_marks_partial_when_records_are_unresolved(
        self,
    ):

        sync_log = (
            AttendanceSyncService.start_sync(
                organization=self.organization,
                device=self.device,
            )
        )

        result = (
            AttendanceSyncService.complete_sync(
                sync_log=sync_log,
                summary={
                    "records_read": 100,
                    "records_in_range": 20,
                    "created": 15,
                    "duplicates": 0,
                    "resolved_existing": 0,
                    "unresolved": 5,
                    "invalid": 0,
                    "attendance_days_rebuilt": 8,
                },
            )
        )

        self.assertEqual(
            result.status,
            AttendanceSyncLog.Status.PARTIAL,
        )

        self.assertEqual(
            result.unresolved,
            5,
        )

    def test_complete_sync_marks_partial_when_records_are_invalid(
        self,
    ):

        sync_log = (
            AttendanceSyncService.start_sync(
                organization=self.organization,
                device=self.device,
            )
        )

        result = (
            AttendanceSyncService.complete_sync(
                sync_log=sync_log,
                summary={
                    "records_read": 100,
                    "records_in_range": 20,
                    "created": 19,
                    "duplicates": 0,
                    "resolved_existing": 0,
                    "unresolved": 0,
                    "invalid": 1,
                    "attendance_days_rebuilt": 9,
                },
            )
        )

        self.assertEqual(
            result.status,
            AttendanceSyncLog.Status.PARTIAL,
        )

        self.assertEqual(
            result.invalid,
            1,
        )

    def test_fail_sync_records_error(
        self,
    ):

        sync_log = (
            AttendanceSyncService.start_sync(
                organization=self.organization,
                device=self.device,
            )
        )

        result = (
            AttendanceSyncService.fail_sync(
                sync_log=sync_log,
                error_message=(
                    "Unable to connect to attendance device."
                ),
                summary={
                    "records_read": 0,
                    "records_in_range": 0,
                },
            )
        )

        self.assertEqual(
            result.status,
            AttendanceSyncLog.Status.FAILED,
        )

        self.assertEqual(
            result.error_message,
            (
                "Unable to connect to attendance device."
            ),
        )

        self.assertIsNotNone(
            result.completed_at,
        )

    def test_cannot_complete_completed_sync(
        self,
    ):

        sync_log = (
            AttendanceSyncService.start_sync(
                organization=self.organization,
                device=self.device,
            )
        )

        AttendanceSyncService.complete_sync(
            sync_log=sync_log,
            summary={},
        )

        with self.assertRaises(
            ValueError
        ):

            AttendanceSyncService.complete_sync(
                sync_log=sync_log,
                summary={},
            )


class DailyAttendanceServiceTests(TestCase):

    def setUp(self):

        self.organization = (
            Organization.objects.create(
                name="Test Company",
                legal_name="Test Company Limited",
            )
        )

        self.employee = (
            EmployeeService.create_employee(
                organization=self.organization,
                first_name="John",
                last_name="Doe",
                company_email="john@testcompany.com",
            )
        )

        self.device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
                vendor="Granding",
                model="FA210-Plus",
                serial_number="FA210-001",
            )
        )

        AttendanceDeviceService.map_employee(
            device=self.device,
            employee=self.employee,
            device_user_id="105",
        )

        self.work_schedule = (
            WorkSchedule.objects.create(
                organization=self.organization,
                code="MON-FRI",
                name="Monday to Friday",
                monday=True,
                tuesday=True,
                wednesday=True,
                thursday=True,
                friday=True,
                saturday=False,
                sunday=False,
                is_active=True,
            )
        )

        EmployeeWorkSchedule.objects.create(
            employee=self.employee,
            work_schedule=self.work_schedule,
            effective_from=datetime(
                2026,
                1,
                1,
            ).date(),
            is_active=True,
        )

        WorkScheduleDay.objects.create(
            work_schedule=self.work_schedule,
            day_of_week=(
                WorkScheduleDay
                .DayOfWeek
                .MONDAY
            ),
            start_time=time(8, 0),
            end_time=time(17, 0),
            grace_period_minutes=15,
        )

    def create_event(
        self,
        occurred_at,
        event_type,
    ):

        return (
            AttendanceEventService.ingest_event(
                organization=self.organization,
                device=self.device,
                device_user_id="105",
                source=(
                    AttendanceEvent.Source.DEVICE
                ),
                event_type=event_type,
                occurred_at=occurred_at,
            )
        )

    def test_workday_with_check_in_and_check_out_is_present(
        self,
    ):

        attendance_date = datetime(
            2026,
            9,
            21,
        ).date()

        self.create_event(
            datetime(
                2026,
                9,
                21,
                8,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_IN,
        )

        self.create_event(
            datetime(
                2026,
                9,
                21,
                17,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_OUT,
        )

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.PRESENT,
        )

        self.assertEqual(
            record.attendance_date,
            attendance_date,
        )

        self.assertEqual(
            record.first_check_in_at.hour,
            8,
        )

        self.assertEqual(
            record.last_check_out_at.hour,
            17,
        )

    def test_check_in_within_grace_period_is_not_late(
        self,
    ):

        attendance_date = datetime(
            2026,
            9,
            21,
        ).date()

        self.create_event(
            datetime(
                2026,
                9,
                21,
                8,
                15,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_IN,
        )

        self.create_event(
            datetime(
                2026,
                9,
                21,
                17,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_OUT,
        )

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.PRESENT,
        )

        self.assertEqual(
            record.late_minutes,
            0,
        )


    def test_check_in_after_grace_period_is_late(
        self,
    ):

        attendance_date = datetime(
            2026,
            9,
            21,
        ).date()

        self.create_event(
            datetime(
                2026,
                9,
                21,
                8,
                23,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_IN,
        )

        self.create_event(
            datetime(
                2026,
                9,
                21,
                17,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_OUT,
        )

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.PRESENT,
        )

        # 08:00 start + 15 minute grace = 08:15.
        # Actual check-in = 08:23.
        # Therefore late = 8 minutes.
        self.assertEqual(
            record.late_minutes,
            8,
        )


    def test_checkout_before_schedule_end_is_early_departure(
        self,
    ):

        attendance_date = datetime(
            2026,
            9,
            21,
        ).date()

        self.create_event(
            datetime(
                2026,
                9,
                21,
                8,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_IN,
        )

        self.create_event(
            datetime(
                2026,
                9,
                21,
                16,
                30,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_OUT,
        )

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.PRESENT,
        )

        # Scheduled end = 17:00.
        # Actual checkout = 16:30.
        # Therefore early departure = 30 minutes.
        self.assertEqual(
            record.early_departure_minutes,
            30,
        )


    def test_checkout_at_schedule_end_has_no_early_departure(
        self,
    ):

        attendance_date = datetime(
            2026,
            9,
            21,
        ).date()

        self.create_event(
            datetime(
                2026,
                9,
                21,
                8,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_IN,
        )

        self.create_event(
            datetime(
                2026,
                9,
                21,
                17,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_OUT,
        )

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.PRESENT,
        )

        self.assertEqual(
            record.early_departure_minutes,
            0,
        )

    def test_workday_without_attendance_is_absent(
        self,
    ):

        attendance_date = datetime(
            2026,
            9,
            21,
        ).date()

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.ABSENT,
        )

        self.assertIsNone(
            record.first_check_in_at,
        )

        self.assertIsNone(
            record.last_check_out_at,
        )

    def test_workday_with_only_check_in_is_incomplete(
        self,
    ):

        attendance_date = datetime(
            2026,
            9,
            21,
        ).date()

        self.create_event(
            datetime(
                2026,
                9,
                21,
                8,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_IN,
        )

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.INCOMPLETE,
        )

        self.assertIsNotNone(
            record.first_check_in_at,
        )

        self.assertIsNone(
            record.last_check_out_at,
        )

    def test_non_working_day_is_off_day(
        self,
    ):

        # Saturday
        attendance_date = datetime(
            2026,
            9,
            19,
        ).date()

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.OFF_DAY,
        )

    def test_public_holiday_is_holiday(
        self,
    ):

        attendance_date = datetime(
            2026,
            9,
            21,
        ).date()

        PublicHoliday.objects.create(
            organization=self.organization,
            date=attendance_date,
            name="Test Public Holiday",
            is_active=True,
        )

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.HOLIDAY,
        )

        self.assertIn(
            "public holiday",
            record.notes.lower(),
        )

    def test_approved_leave_is_on_leave(
        self,
    ):

        attendance_date = datetime(
            2026,
            9,
            21,
        ).date()

        leave_type = (
            LeaveType.objects.create(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
                is_active=True,
            )
        )

        LeaveRequest.objects.create(
            organization=self.organization,
            employee=self.employee,
            leave_type=leave_type,
            start_date=attendance_date,
            end_date=attendance_date,
            requested_days=1,
            reason="Annual leave",
            status=LeaveRequest.Status.APPROVED,
        )

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.ON_LEAVE,
        )

        self.assertIn(
            "leave",
            record.notes.lower(),
        )

    def test_pending_leave_does_not_make_employee_on_leave(
        self,
    ):

        attendance_date = datetime(
            2026,
            9,
            21,
        ).date()

        leave_type = (
            LeaveType.objects.create(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
                is_active=True,
            )
        )

        LeaveRequest.objects.create(
            organization=self.organization,
            employee=self.employee,
            leave_type=leave_type,
            start_date=attendance_date,
            end_date=attendance_date,
            requested_days=1,
            reason="Annual leave",
            status=LeaveRequest.Status.SUBMITTED,
        )

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.ABSENT,
        )

    def test_leave_takes_priority_over_attendance(
        self,
    ):

        attendance_date = datetime(
            2026,
            9,
            21,
        ).date()

        self.create_event(
            datetime(
                2026,
                9,
                21,
                8,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_IN,
        )

        self.create_event(
            datetime(
                2026,
                9,
                21,
                17,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_OUT,
        )

        leave_type = (
            LeaveType.objects.create(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
                is_active=True,
            )
        )

        LeaveRequest.objects.create(
            organization=self.organization,
            employee=self.employee,
            leave_type=leave_type,
            start_date=attendance_date,
            end_date=attendance_date,
            requested_days=1,
            reason="Annual leave",
            status=LeaveRequest.Status.APPROVED,
        )

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.ON_LEAVE,
        )

    def test_holiday_takes_priority_over_attendance(
        self,
    ):

        attendance_date = datetime(
            2026,
            9,
            21,
        ).date()

        self.create_event(
            datetime(
                2026,
                9,
                21,
                8,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_IN,
        )

        self.create_event(
            datetime(
                2026,
                9,
                21,
                17,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_OUT,
        )

        PublicHoliday.objects.create(
            organization=self.organization,
            date=attendance_date,
            name="Test Public Holiday",
            is_active=True,
        )

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.HOLIDAY,
        )

    def test_no_work_schedule_keeps_event_derived_status(
        self,
    ):

        EmployeeWorkSchedule.objects.filter(
            employee=self.employee,
        ).update(
            is_active=False,
        )

        attendance_date = datetime(
            2026,
            9,
            21,
        ).date()

        self.create_event(
            datetime(
                2026,
                9,
                21,
                8,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_IN,
        )

        self.create_event(
            datetime(
                2026,
                9,
                21,
                17,
                0,
                tzinfo=dt_timezone.utc,
            ),
            AttendanceEvent.EventType.CHECK_OUT,
        )

        record = (
            DailyAttendanceService.process_employee_day(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.PRESENT,
        )

        self.assertIn(
            "no active work schedule",
            record.notes.lower(),
        )




class WorkScheduleDayTests(TestCase):

    def setUp(self):

        self.organization = (
            Organization.objects.create(
                name="Test Company",
                legal_name="Test Company Limited",
            )
        )

        self.work_schedule = (
            WorkSchedule.objects.create(
                organization=self.organization,
                code="STANDARD",
                name="Standard Work Schedule",
                monday=True,
                tuesday=True,
                wednesday=True,
                thursday=True,
                friday=True,
                saturday=False,
                sunday=False,
                is_active=True,
            )
        )

    def test_create_work_schedule_day(
        self,
    ):

        schedule_day = (
            WorkScheduleDay.objects.create(
                work_schedule=self.work_schedule,
                day_of_week=(
                    WorkScheduleDay
                    .DayOfWeek
                    .MONDAY
                ),
                start_time=datetime.strptime(
                    "08:00",
                    "%H:%M",
                ).time(),
                end_time=datetime.strptime(
                    "17:00",
                    "%H:%M",
                ).time(),
                grace_period_minutes=15,
            )
        )

        self.assertEqual(
            schedule_day.work_schedule,
            self.work_schedule,
        )

        self.assertEqual(
            schedule_day.day_of_week,
            WorkScheduleDay.DayOfWeek.MONDAY,
        )

        self.assertEqual(
            schedule_day.start_time.hour,
            8,
        )

        self.assertEqual(
            schedule_day.end_time.hour,
            17,
        )

        self.assertEqual(
            schedule_day.grace_period_minutes,
            15,
        )

    def test_schedule_day_string_representation(
        self,
    ):

        schedule_day = (
            WorkScheduleDay.objects.create(
                work_schedule=self.work_schedule,
                day_of_week=(
                    WorkScheduleDay
                    .DayOfWeek
                    .MONDAY
                ),
                start_time=datetime.strptime(
                    "08:00",
                    "%H:%M",
                ).time(),
                end_time=datetime.strptime(
                    "17:00",
                    "%H:%M",
                ).time(),
            )
        )

        self.assertEqual(
            str(schedule_day),
            "Standard Work Schedule - Monday",
        )

    def test_same_schedule_cannot_have_duplicate_day(
        self,
    ):

        WorkScheduleDay.objects.create(
            work_schedule=self.work_schedule,
            day_of_week=(
                WorkScheduleDay
                .DayOfWeek
                .MONDAY
            ),
            start_time=datetime.strptime(
                "08:00",
                "%H:%M",
            ).time(),
            end_time=datetime.strptime(
                "17:00",
                "%H:%M",
            ).time(),
        )

        with self.assertRaises(IntegrityError): 

            WorkScheduleDay.objects.create(
                work_schedule=self.work_schedule,
                day_of_week=(
                    WorkScheduleDay
                    .DayOfWeek
                    .MONDAY
                ),
                start_time=datetime.strptime(
                    "09:00",
                    "%H:%M",
                ).time(),
                end_time=datetime.strptime(
                    "18:00",
                    "%H:%M",
                ).time(),
            )

    def test_same_schedule_can_have_different_days(
        self,
    ):

        monday = (
            WorkScheduleDay.objects.create(
                work_schedule=self.work_schedule,
                day_of_week=(
                    WorkScheduleDay
                    .DayOfWeek
                    .MONDAY
                ),
                start_time=datetime.strptime(
                    "08:00",
                    "%H:%M",
                ).time(),
                end_time=datetime.strptime(
                    "17:00",
                    "%H:%M",
                ).time(),
            )
        )

        friday = (
            WorkScheduleDay.objects.create(
                work_schedule=self.work_schedule,
                day_of_week=(
                    WorkScheduleDay
                    .DayOfWeek
                    .FRIDAY
                ),
                start_time=datetime.strptime(
                    "08:00",
                    "%H:%M",
                ).time(),
                end_time=datetime.strptime(
                    "15:00",
                    "%H:%M",
                ).time(),
            )
        )

        self.assertNotEqual(
            monday.id,
            friday.id,
        )

        self.assertEqual(
            monday.day_of_week,
            WorkScheduleDay.DayOfWeek.MONDAY,
        )

        self.assertEqual(
            friday.day_of_week,
            WorkScheduleDay.DayOfWeek.FRIDAY,
        )


class AttendanceRecordCheckoutSourceTests(TestCase):

    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Organization",
        )

        self.employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
        )

    def test_new_attendance_record_has_no_checkout_source(self):
        record = AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date="2026-08-27",
        )

        self.assertEqual(
            record.checkout_source,
            AttendanceRecord.CheckoutSource.NONE,
        )

    def test_system_checkout_source_can_be_stored(self):
        record = AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date="2026-08-27",
            last_check_out_at=timezone.now(),
            checkout_source=(
                AttendanceRecord
                .CheckoutSource
                .SYSTEM
            ),
        )

        self.assertEqual(
            record.checkout_source,
            AttendanceRecord.CheckoutSource.SYSTEM,
        )


class AttendanceReconciliationTests(TestCase):

    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Organization",
            automatic_attendance_checkout_enabled=True,
        )

        self.employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
        )

        self.work_schedule = WorkSchedule.objects.create(
            organization=self.organization,
            code="STANDARD",
            name="Standard Work Schedule",
            monday=True,
            tuesday=True,
            wednesday=True,
            thursday=True,
            friday=True,
            saturday=False,
            sunday=False,
        )

        WorkScheduleDay.objects.create(
            work_schedule=self.work_schedule,
            day_of_week=0,
            start_time=time(8, 0),
            end_time=time(17, 0),
            grace_period_minutes=15,
        )

        WorkScheduleDay.objects.create(
            work_schedule=self.work_schedule,
            day_of_week=1,
            start_time=time(8, 0),
            end_time=time(17, 0),
            grace_period_minutes=15,
        )

        WorkScheduleDay.objects.create(
            work_schedule=self.work_schedule,
            day_of_week=2,
            start_time=time(8, 0),
            end_time=time(17, 0),
            grace_period_minutes=15,
        )

        WorkScheduleDay.objects.create(
            work_schedule=self.work_schedule,
            day_of_week=3,
            start_time=time(8, 0),
            end_time=time(17, 0),
            grace_period_minutes=15,
        )

        WorkScheduleDay.objects.create(
            work_schedule=self.work_schedule,
            day_of_week=4,
            start_time=time(8, 0),
            end_time=time(17, 0),
            grace_period_minutes=15,
        )

        EmployeeWorkSchedule.objects.create(
            employee=self.employee,
            work_schedule=self.work_schedule,
            effective_from=date(2026, 8, 24),
        )

    def create_check_in(
        self,
        occurred_at,
    ):
        return AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=occurred_at,
            processing_status=(
                AttendanceEvent
                .ProcessingStatus
                .PROCESSED
            ),
        )

    def create_check_out(
        self,
        occurred_at,
    ):
        return AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_OUT,
            occurred_at=occurred_at,
            processing_status=(
                AttendanceEvent
                .ProcessingStatus
                .PROCESSED
            ),
        )

    def test_open_record_is_closed_at_11pm(self):
        attendance_date = date(2026, 8, 24)

        check_in = timezone.make_aware(
            datetime(
                2026,
                8,
                24,
                8,
                5,
            ),
        )

        self.create_check_in(
            occurred_at=check_in,
        )

        record = (
            AttendanceRecordService
            .rebuild_daily_record(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        record = (
            AttendanceRecordService
            .reconcile_open_attendance_record(
                record=record,
            )
        )

        expected_checkout = timezone.make_aware(
            datetime(
                2026,
                8,
                24,
                23,
                0,
            ),
        )

        self.assertIsNotNone(record)

        self.assertEqual(
            record.last_check_out_at,
            expected_checkout,
        )

        self.assertEqual(
            record.checkout_source,
            AttendanceRecord
            .CheckoutSource
            .SYSTEM,
        )

        self.assertEqual(
            record.worked_minutes,
            895,
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.PRESENT,
        )

    def test_actual_checkout_is_never_overwritten(self):
        attendance_date = date(2026, 8, 24)

        check_in = timezone.make_aware(
            datetime(
                2026,
                8,
                24,
                8,
                5,
            ),
        )

        check_out = timezone.make_aware(
            datetime(
                2026,
                8,
                24,
                20,
                30,
            ),
        )

        self.create_check_in(
            occurred_at=check_in,
        )

        self.create_check_out(
            occurred_at=check_out,
        )

        record = (
            AttendanceRecordService
            .rebuild_daily_record(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        result = (
            AttendanceRecordService
            .reconcile_open_attendance_record(
                record=record,
            )
        )

        self.assertIsNone(result)

        record.refresh_from_db()

        self.assertEqual(
            record.last_check_out_at,
            check_out,
        )

        self.assertEqual(
            record.checkout_source,
            AttendanceRecord
            .CheckoutSource
            .DEVICE,
        )

    def test_disabled_automatic_checkout_does_nothing(self):
        self.organization.automatic_attendance_checkout_enabled = False
        self.organization.save(
            update_fields=[
                "automatic_attendance_checkout_enabled",
            ]
        )

        attendance_date = date(2026, 8, 24)

        check_in = timezone.make_aware(
            datetime(
                2026,
                8,
                24,
                8,
                5,
            ),
        )

        self.create_check_in(
            occurred_at=check_in,
        )

        record = (
            AttendanceRecordService
            .rebuild_daily_record(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        result = (
            AttendanceRecordService
            .reconcile_open_attendance_record(
                record=record,
            )
        )

        self.assertIsNone(result)

        record.refresh_from_db()

        self.assertIsNone(
            record.last_check_out_at,
        )

        self.assertEqual(
            record.checkout_source,
            AttendanceRecord
            .CheckoutSource
            .NONE,
        )

    def test_friday_record_is_closed_using_friday_date(self):
        friday = date(2026, 8, 28)

        check_in = timezone.make_aware(
            datetime(
                2026,
                8,
                28,
                8,
                5,
            ),
        )

        self.create_check_in(
            occurred_at=check_in,
        )

        record = (
            AttendanceRecordService
            .rebuild_daily_record(
                employee=self.employee,
                attendance_date=friday,
            )
        )

        # Simulates the Friday 11 PM reconciliation
        # being missed because the server was offline.
        #
        # The important assertion is that reconciliation
        # uses the attendance date, not the date on which
        # the server happens to restart.
        result = (
            AttendanceRecordService
            .reconcile_open_attendance_record(
                record=record,
            )
        )

        expected_checkout = timezone.make_aware(
            datetime(
                2026,
                8,
                28,
                23,
                0,
            ),
        )

        self.assertIsNotNone(result)

        self.assertEqual(
            result.attendance_date,
            friday,
        )

        self.assertEqual(
            result.last_check_out_at,
            expected_checkout,
        )

        self.assertEqual(
            result.last_check_out_at.date(),
            friday,
        )

        self.assertEqual(
            result.checkout_source,
            AttendanceRecord
            .CheckoutSource
            .SYSTEM,
        )

    def test_off_day_is_not_system_closed(self):
        saturday = date(2026, 8, 29)

        check_in = timezone.make_aware(
            datetime(
                2026,
                8,
                29,
                8,
                5,
            ),
        )

        self.create_check_in(
            occurred_at=check_in,
        )

        record = (
            AttendanceRecordService
            .rebuild_daily_record(
                employee=self.employee,
                attendance_date=saturday,
            )
        )

        result = (
            AttendanceRecordService
            .reconcile_open_attendance_record(
                record=record,
            )
        )

        self.assertIsNone(result)

        record.refresh_from_db()

        self.assertIsNone(
            record.last_check_out_at,
        )

        self.assertEqual(
            record.checkout_source,
            AttendanceRecord
            .CheckoutSource
            .NONE,
        )

    def test_public_holiday_is_not_system_closed(self):
        attendance_date = date(2026, 8, 24)

        PublicHoliday.objects.create(
            organization=self.organization,
            date=attendance_date,
            name="Test Public Holiday",
            is_active=True,
        )

        check_in = timezone.make_aware(
            datetime(
                2026,
                8,
                24,
                8,
                5,
            ),
        )

        self.create_check_in(
            occurred_at=check_in,
        )

        record = (
            AttendanceRecordService
            .rebuild_daily_record(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        result = (
            AttendanceRecordService
            .reconcile_open_attendance_record(
                record=record,
            )
        )

        self.assertIsNone(result)

        record.refresh_from_db()

        self.assertIsNone(
            record.last_check_out_at,
        )

    def test_approved_leave_is_not_system_closed(self):
        attendance_date = date(2026, 8, 24)

        leave_type = LeaveType.objects.create(
            organization=self.organization,
            code="ANNUAL",
            name="Annual Leave",
            is_active=True,
        )

        LeaveRequest.objects.create(
            organization=self.organization,
            employee=self.employee,
            leave_type=leave_type,
            start_date=attendance_date,
            end_date=attendance_date,
            requested_days=1,
            reason="Annual leave",
            status=LeaveRequest.Status.APPROVED,
        )

        check_in = timezone.make_aware(
            datetime(
                2026,
                8,
                24,
                8,
                5,
            ),
        )

        self.create_check_in(
            occurred_at=check_in,
        )

        record = (
            AttendanceRecordService
            .rebuild_daily_record(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        result = (
            AttendanceRecordService
            .reconcile_open_attendance_record(
                record=record,
            )
        )

        self.assertIsNone(result)

        record.refresh_from_db()

        self.assertIsNone(
            record.last_check_out_at,
        )

    def test_record_without_check_in_is_not_system_closed(self):
        attendance_date = date(2026, 8, 24)

        record = (
            AttendanceRecordService
            .rebuild_daily_record(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )

        result = (
            AttendanceRecordService
            .reconcile_open_attendance_record(
                record=record,
            )
        )

        self.assertIsNone(result)

        record.refresh_from_db()

        self.assertIsNone(
            record.last_check_out_at,
        )

        self.assertEqual(
            record.checkout_source,
            AttendanceRecord
            .CheckoutSource
            .NONE,
        )
    
    def test_system_checkout_survives_daily_record_rebuild(self):
        attendance_date = date(2026, 8, 24)
    
        check_in = timezone.make_aware(
            datetime(
                2026,
                8,
                24,
                8,
                5,
            )
        )
    
        AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=check_in,
            processing_status=(
                AttendanceEvent.ProcessingStatus.PROCESSED
            ),
        )
    
        record = AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date=attendance_date,
            first_check_in_at=check_in,
            status=AttendanceRecord.Status.INCOMPLETE,
        )
    
        reconciled_record = (
            AttendanceRecordService
            .reconcile_open_attendance_record(
                record=record,
            )
        )
    
        self.assertIsNotNone(
            reconciled_record,
        )
    
        system_checkout_time = timezone.make_aware(
            datetime(
                2026,
                8,
                24,
                23,
                0,
            )
        )
    
        self.assertTrue(
            AttendanceEvent.objects.filter(
                employee=self.employee,
                source=AttendanceEvent.Source.SYSTEM,
                event_type=AttendanceEvent.EventType.CHECK_OUT,
                occurred_at=system_checkout_time,
            ).exists()
        )
    
        rebuilt_record = (
            AttendanceRecordService
            .rebuild_daily_record(
                employee=self.employee,
                attendance_date=attendance_date,
            )
        )
    
        self.assertEqual(
            rebuilt_record.last_check_out_at,
            system_checkout_time,
        )
    
        self.assertEqual(
            rebuilt_record.checkout_source,
            AttendanceRecord.CheckoutSource.SYSTEM,
        )
    
        self.assertEqual(
            rebuilt_record.status,
            AttendanceRecord.Status.PRESENT,
        )
    
class AttendanceReconciliationTaskTests(TestCase):

    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Organization",
            automatic_attendance_checkout_enabled=True,
        )

        self.employee = Employee.objects.create(
            organization=self.organization,
            employee_number="EMP-001",
        )

        self.work_schedule = WorkSchedule.objects.create(
            organization=self.organization,
            code="STANDARD",
            name="Standard Work Schedule",
            monday=True,
            tuesday=True,
            wednesday=True,
            thursday=True,
            friday=True,
            saturday=False,
            sunday=False,
        )

        EmployeeWorkSchedule.objects.create(
            employee=self.employee,
            work_schedule=self.work_schedule,
            effective_from=date(2026, 9, 1),
        )

        WorkScheduleDay.objects.create(
            work_schedule=self.work_schedule,
            day_of_week=WorkScheduleDay.DayOfWeek.FRIDAY,
            start_time=time(8, 0),
            end_time=time(17, 0),
        )

    def test_task_reconciles_historical_open_record(self):
        attendance_date = date(2026, 9, 18)

        check_in = timezone.make_aware(
            datetime(
                2026,
                9,
                18,
                8,
                10,
            )
        )

        AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=check_in,
            processing_status=(
                AttendanceEvent.ProcessingStatus.PROCESSED
            ),
        )

        record = AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date=attendance_date,
            first_check_in_at=check_in,
            status=AttendanceRecord.Status.INCOMPLETE,
        )

        result = reconcile_open_attendance_records()

        record.refresh_from_db()

        self.assertEqual(
            result["records_found"],
            1,
        )

        self.assertEqual(
            result["records_reconciled"],
            1,
        )

        self.assertEqual(
            result["records_failed"],
            0,
        )

        self.assertEqual(
            record.last_check_out_at,
            timezone.make_aware(
                datetime(
                    2026,
                    9,
                    18,
                    23,
                    0,
                )
            ),
        )

        self.assertEqual(
            record.checkout_source,
            AttendanceRecord.CheckoutSource.SYSTEM,
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.PRESENT,
        )

    def test_task_reconciles_multiple_open_records(self):
        second_employee = Employee.objects.create(
            organization=self.organization,
            employee_number="EMP-002",
        )

        EmployeeWorkSchedule.objects.create(
            employee=second_employee,
            work_schedule=self.work_schedule,
            effective_from=date(2026, 9, 1),
        )

        attendance_date = date(2026, 9, 18)

        first_record = AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date=attendance_date,
            first_check_in_at=timezone.make_aware(
                datetime(2026, 9, 18, 8, 10)
            ),
            status=AttendanceRecord.Status.INCOMPLETE,
        )

        second_record = AttendanceRecord.objects.create(
            organization=self.organization,
            employee=second_employee,
            attendance_date=attendance_date,
            first_check_in_at=timezone.make_aware(
                datetime(2026, 9, 18, 8, 20)
            ),
            status=AttendanceRecord.Status.INCOMPLETE,
        )

        result = reconcile_open_attendance_records()

        first_record.refresh_from_db()
        second_record.refresh_from_db()

        self.assertEqual(result["records_found"], 2)
        self.assertEqual(result["records_reconciled"], 2)
        self.assertEqual(result["records_skipped"], 0)
        self.assertEqual(result["records_failed"], 0)

        self.assertEqual(
            first_record.checkout_source,
            AttendanceRecord.CheckoutSource.SYSTEM,
        )
        self.assertEqual(
            second_record.checkout_source,
            AttendanceRecord.CheckoutSource.SYSTEM,
        )

    def test_task_reconciles_eligible_record_and_skips_ineligible_record(self):
        saturday_employee = Employee.objects.create(
            organization=self.organization,
            employee_number="EMP-002",
        )

        EmployeeWorkSchedule.objects.create(
            employee=saturday_employee,
            work_schedule=self.work_schedule,
            effective_from=date(2026, 9, 1),
        )

        attendance_date = date(2026, 9, 19)  # Saturday

        eligible_record = AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date=date(2026, 9, 18),  # Friday
            first_check_in_at=timezone.make_aware(
                datetime(2026, 9, 18, 8, 10)
            ),
            status=AttendanceRecord.Status.INCOMPLETE,
        )

        skipped_record = AttendanceRecord.objects.create(
            organization=self.organization,
            employee=saturday_employee,
            attendance_date=attendance_date,
            first_check_in_at=timezone.make_aware(
                datetime(2026, 9, 19, 8, 10)
            ),
            status=AttendanceRecord.Status.INCOMPLETE,
        )

        result = reconcile_open_attendance_records()

        eligible_record.refresh_from_db()
        skipped_record.refresh_from_db()

        self.assertEqual(result["records_found"], 2)
        self.assertEqual(result["records_reconciled"], 1)
        self.assertEqual(result["records_skipped"], 1)
        self.assertEqual(result["records_failed"], 0)

        self.assertEqual(
            eligible_record.checkout_source,
            AttendanceRecord.CheckoutSource.SYSTEM,
        )

        self.assertIsNone(
            skipped_record.last_check_out_at,
        )

        self.assertEqual(
            skipped_record.checkout_source,
            AttendanceRecord.CheckoutSource.NONE,
        )

    def test_task_skips_record_when_automatic_checkout_is_disabled(self):
        self.organization.automatic_attendance_checkout_enabled = False
        self.organization.save(
            update_fields=["automatic_attendance_checkout_enabled"]
        )

        record = AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date=date(2026, 9, 18),
            first_check_in_at=timezone.make_aware(
                datetime(2026, 9, 18, 8, 10)
            ),
            status=AttendanceRecord.Status.INCOMPLETE,
        )

        result = reconcile_open_attendance_records()

        record.refresh_from_db()

        self.assertEqual(result["records_found"], 0)
        self.assertEqual(result["records_reconciled"], 0)
        self.assertEqual(result["records_skipped"], 0)
        self.assertEqual(result["records_failed"], 0)

        self.assertIsNone(record.last_check_out_at)
        self.assertEqual(
            record.checkout_source,
            AttendanceRecord.CheckoutSource.NONE,
        )

