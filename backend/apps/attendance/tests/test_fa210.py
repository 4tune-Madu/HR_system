from datetime import datetime, timezone as dt_timezone
from unittest.mock import MagicMock, patch
from django.utils import timezone

from django.test import TestCase

from apps.attendance.models import (
    AttendanceDevice,
    AttendanceDeviceEmployee,
    AttendanceEvent,
    AttendanceException,
    AttendanceRecord,
    AttendanceSyncLog,
)
from apps.attendance.integrations.fa210 import (
    FA210Adapter,
)
from apps.employee.services import (
    EmployeeService,
)
from apps.organization.models import (
    Organization,
)

from datetime import datetime, timezone as dt_timezone
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from apps.organization.models import Organization
from apps.employee.services import EmployeeService

from apps.attendance.models import (
    AttendanceDevice,
    AttendanceDeviceEmployee,
    AttendanceEvent,
    AttendanceRecord,
    AttendanceException,
    
)

from apps.attendance.services import (
    AttendanceDeviceService,
    AttendanceSyncService,
)

from apps.attendance.integrations.fa210 import (
    FA210Adapter,
)

class FA210NormalizationTests(TestCase):

    def setUp(self):

        self.organization = (
            Organization.objects.create(
                name="Test Company",
                legal_name="Test Company Limited",
            )
        )

        self.device = (
            AttendanceDevice.objects.create(
                organization=self.organization,
                name="Main Entrance",
                vendor="Granding",
                model="FA210-Plus",
                serial_number="8029243900402",
                ip_address="10.0.0.151",
                port=4370,
                connection_type=(
                    AttendanceDevice
                    .ConnectionType.NETWORK
                ),
                is_active=True,
            )
        )

        self.adapter = FA210Adapter(
            device=self.device
        )

    def make_record(
        self,
        uid,
        user_id,
        timestamp,
        status=1,
        punch=255,
    ):
        record = MagicMock()

        record.uid = uid
        record.user_id = user_id
        record.timestamp = timestamp
        record.status = status
        record.punch = punch

        return record

    def test_undefined_punches_alternate_in_and_out(
        self,
    ):

        records = [
            self.make_record(
                uid=66,
                user_id="23",
                timestamp=datetime(
                    2026,
                    9,
                    21,
                    8,
                    0,
                ),
            ),
            self.make_record(
                uid=67,
                user_id="23",
                timestamp=datetime(
                    2026,
                    9,
                    21,
                    17,
                    0,
                ),
            ),
        ]

        normalized = (
            self.adapter
            .normalize_attendance_records(
                records
            )
        )

        self.assertEqual(
            normalized[0]["event_type"],
            AttendanceEvent
            .EventType
            .CHECK_IN,
        )

        self.assertEqual(
            normalized[1]["event_type"],
            AttendanceEvent
            .EventType
            .CHECK_OUT,
        )

        self.assertTrue(
            normalized[0][
                "inferred_event_type"
            ]
        )

        self.assertTrue(
            normalized[1][
                "inferred_event_type"
            ]
        )

    def test_explicit_punch_state_takes_precedence(
        self,
    ):

        records = [
            self.make_record(
                uid=66,
                user_id="23",
                timestamp=datetime(
                    2026,
                    9,
                    21,
                    8,
                    0,
                ),
                punch=0,
            ),
            self.make_record(
                uid=67,
                user_id="23",
                timestamp=datetime(
                    2026,
                    9,
                    21,
                    17,
                    0,
                ),
                punch=1,
            ),
        ]

        normalized = (
            self.adapter
            .normalize_attendance_records(
                records
            )
        )

        self.assertEqual(
            normalized[0]["event_type"],
            AttendanceEvent
            .EventType
            .CHECK_IN,
        )

        self.assertEqual(
            normalized[1]["event_type"],
            AttendanceEvent
            .EventType
            .CHECK_OUT,
        )

        self.assertFalse(
            normalized[0][
                "inferred_event_type"
            ]
        )

        self.assertFalse(
            normalized[1][
                "inferred_event_type"
            ]
        )


class FA210SyncTests(TestCase):

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
                first_name="Olumide",
                last_name="Test",
                company_email="olumide@testcompany.com",
            )
        )

        self.device = (
            AttendanceDevice.objects.create(
                organization=self.organization,
                name="Main Entrance",
                vendor="Granding",
                model="FA210-Plus",
                serial_number="8029243900402",
                ip_address="10.0.0.151",
                port=4370,
                connection_type=(
                    AttendanceDevice
                    .ConnectionType.NETWORK
                ),
                is_active=True,
            )
        )

        AttendanceDeviceEmployee.objects.create(
            device=self.device,
            employee=self.employee,
            device_user_id="23",
            display_name="Olumide",
        )

        self.adapter = FA210Adapter(
            device=self.device
        )

    def make_record(
        self,
        uid,
        timestamp,
        user_id="23",
    ):
        record = MagicMock()

        record.uid = uid
        record.user_id = user_id
        record.timestamp = timestamp
        record.status = 1
        record.punch = 255

        return record

    @patch(
        "apps.attendance.integrations.fa210.ZK"
    )
    def test_sync_creates_attendance_events_and_record(
        self,
        zk_class,
    ):

        zk_connection = MagicMock()

        zk_instance = MagicMock()

        zk_instance.connect.return_value = (
            zk_connection
        )

        zk_connection.get_attendance.return_value = [
            self.make_record(
                uid=66,
                timestamp=datetime(
                    2026,
                    9,
                    21,
                    8,
                    0,
                ),
            ),
            self.make_record(
                uid=67,
                timestamp=datetime(
                    2026,
                    9,
                    21,
                    17,
                    0,
                ),
            ),
        ]

        zk_class.return_value = (
            zk_instance
        )

        result = (
            self.adapter
            .sync_attendance()
        )

        self.assertEqual(
            result["records_read"],
            2,
        )

        self.assertEqual(
            result["created"],
            2,
        )

        self.assertEqual(
            AttendanceEvent.objects.count(),
            2,
        )

        record = (
            AttendanceRecord.objects.get(
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
            540,
        )

    @patch(
        "apps.attendance.integrations.fa210.ZK"
    )
    def test_sync_is_idempotent(
        self,
        zk_class,
    ):

        records = [
            self.make_record(
                uid=66,
                timestamp=datetime(
                    2026,
                    9,
                    21,
                    8,
                    0,
                ),
            ),
            self.make_record(
                uid=67,
                timestamp=datetime(
                    2026,
                    9,
                    21,
                    17,
                    0,
                ),
            ),
        ]

        zk_connection = MagicMock()

        zk_connection.get_attendance.return_value = (
            records
        )

        zk_instance = MagicMock()

        zk_instance.connect.return_value = (
            zk_connection
        )

        zk_class.return_value = (
            zk_instance
        )

        first = (
            self.adapter
            .sync_attendance()
        )

        second = (
            self.adapter
            .sync_attendance()
        )

        self.assertEqual(
            first["created"],
            2,
        )

        self.assertEqual(
            second["created"],
            0,
        )

        self.assertEqual(
            second["duplicates"],
            2,
        )

        self.assertEqual(
            AttendanceEvent.objects.count(),
            2,
        )

    @patch(
        "apps.attendance.integrations.fa210.ZK"
    )
    def test_unknown_device_user_is_preserved_as_unresolved_event(
        self,
        zk_class,
    ):

        unknown_record = (
            self.make_record(
                uid=99,
                user_id="999",
                timestamp=datetime(
                    2026,
                    9,
                    21,
                    8,
                    0,
                ),
            )
        )

        zk_connection = MagicMock()

        zk_connection.get_attendance.return_value = [
            unknown_record
        ]

        zk_instance = MagicMock()

        zk_instance.connect.return_value = (
            zk_connection
        )

        zk_class.return_value = (
            zk_instance
        )

        result = (
            self.adapter
            .sync_attendance()
        )

        event = (
            AttendanceEvent.objects.get()
        )

        self.assertEqual(
            result["unresolved"],
            1,
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

    @patch(
        "apps.attendance.integrations.fa210.ZK"
    )
    def test_device_last_sync_is_updated(
        self,
        zk_class,
    ):

        zk_connection = MagicMock()

        zk_connection.get_attendance.return_value = []

        zk_instance = MagicMock()

        zk_instance.connect.return_value = (
            zk_connection
        )

        zk_class.return_value = (
            zk_instance
        )

        self.assertIsNone(
            self.device.last_sync_at
        )

        self.adapter.sync_attendance()

        self.device.refresh_from_db()

        self.assertIsNotNone(
            self.device.last_sync_at
        )


class FA210SynchronizationTests(
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
                connection_type=(
                    AttendanceDevice
                    .ConnectionType.NETWORK
                ),
                ip_address="192.168.1.50",
                port=4370,
            )
        )

    def create_mapping(
        self,
        device_user_id="105",
    ):
        return (
            AttendanceDeviceService.map_employee(
                device=self.device,
                employee=self.employee,
                device_user_id=device_user_id,
            )
        )

    def create_record(
        self,
        *,
        uid,
        user_id,
        occurred_at,
        status=1,
        punch=255,
    ):
        return SimpleNamespace(
            uid=uid,
            user_id=user_id,
            timestamp=occurred_at,
            status=status,
            punch=punch,
        )

    @patch.object(
        FA210Adapter,
        "connect",
    )
    @patch.object(
        FA210Adapter,
        "disconnect",
    )
    @patch.object(
        FA210Adapter,
        "get_attendance",
    )
    def test_sync_creates_events_and_attendance_record(
        self,
        mock_get_attendance,
        mock_disconnect,
        mock_connect,
    ):

        self.create_mapping()

        check_in = datetime(
            2026,
            9,
            21,
            8,
            0,
            tzinfo=dt_timezone.utc,
        )

        check_out = datetime(
            2026,
            9,
            21,
            17,
            0,
            tzinfo=dt_timezone.utc,
        )

        mock_get_attendance.return_value = [
            self.create_record(
                uid=1,
                user_id="105",
                occurred_at=check_in,
            ),
            self.create_record(
                uid=2,
                user_id="105",
                occurred_at=check_out,
            ),
        ]

        adapter = FA210Adapter(
            device=self.device,
        )

        result = adapter.sync_attendance()

        self.assertEqual(
            result["records_read"],
            2,
        )

        self.assertEqual(
            result["created"],
            2,
        )

        self.assertEqual(
            result["duplicates"],
            0,
        )

        self.assertEqual(
            AttendanceEvent.objects.count(),
            2,
        )

        record = (
            AttendanceRecord.objects.get(
                employee=self.employee,
                attendance_date=check_in.date(),
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.PRESENT,
        )

        self.assertEqual(
            record.worked_minutes,
            540,
        )

    @patch.object(
        FA210Adapter,
        "connect",
    )
    @patch.object(
        FA210Adapter,
        "disconnect",
    )
    @patch.object(
        FA210Adapter,
        "get_attendance",
    )
    def test_sync_is_idempotent(
        self,
        mock_get_attendance,
        mock_disconnect,
        mock_connect,
    ):

        self.create_mapping()

        occurred_at = datetime(
            2026,
            9,
            21,
            8,
            0,
            tzinfo=dt_timezone.utc,
        )

        mock_get_attendance.return_value = [
            self.create_record(
                uid=1,
                user_id="105",
                occurred_at=occurred_at,
            ),
        ]

        adapter = FA210Adapter(
            device=self.device,
        )

        first_result = (
            adapter.sync_attendance()
        )

        second_result = (
            adapter.sync_attendance()
        )

        self.assertEqual(
            first_result["created"],
            1,
        )

        self.assertEqual(
            second_result["created"],
            0,
        )

        self.assertEqual(
            second_result["duplicates"],
            1,
        )

        self.assertEqual(
            AttendanceEvent.objects.count(),
            1,
        )

    @patch.object(
        FA210Adapter,
        "connect",
    )
    @patch.object(
        FA210Adapter,
        "disconnect",
    )
    @patch.object(
        FA210Adapter,
        "get_attendance",
    )
    def test_unresolved_employee_event_is_failed(
        self,
        mock_get_attendance,
        mock_disconnect,
        mock_connect,
    ):

        occurred_at = datetime(
            2026,
            9,
            21,
            8,
            0,
            tzinfo=dt_timezone.utc,
        )

        mock_get_attendance.return_value = [
            self.create_record(
                uid=1,
                user_id="999",
                occurred_at=occurred_at,
            ),
        ]

        adapter = FA210Adapter(
            device=self.device,
        )

        result = adapter.sync_attendance()

        self.assertEqual(
            result["unresolved"],
            1,
        )

        event = (
            AttendanceEvent.objects.get()
        )

        self.assertIsNone(
            event.employee_id,
        )

        self.assertEqual(
            event.processing_status,
            AttendanceEvent
            .ProcessingStatus
            .PENDING,
        )

        self.assertTrue(
            AttendanceException.objects.filter(
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
            ).exists()
        )

    @patch.object(
        FA210Adapter,
        "connect",
    )
    @patch.object(
        FA210Adapter,
        "disconnect",
    )
    @patch.object(
        FA210Adapter,
        "get_attendance",
    )
    def test_existing_unresolved_event_is_resolved_after_mapping(
        self,
        mock_get_attendance,
        mock_disconnect,
        mock_connect,
    ):

        occurred_at = datetime(
            2026,
            9,
            21,
            8,
            0,
            tzinfo=dt_timezone.utc,
        )

        mock_get_attendance.return_value = [
            self.create_record(
                uid=1,
                user_id="999",
                occurred_at=occurred_at,
            ),
        ]

        adapter = FA210Adapter(
            device=self.device,
        )

        first_result = (
            adapter.sync_attendance()
        )

        self.assertEqual(
            first_result["unresolved"],
            1,
        )

        event = (
            AttendanceEvent.objects.get()
        )

        self.assertIsNone(
            event.employee_id,
        )

        self.create_mapping(
            device_user_id="999",
        )

        second_result = (
            adapter.sync_attendance()
        )

        event.refresh_from_db()

        self.assertEqual(
            second_result["resolved_existing"],
            1,
        )

        self.assertEqual(
            event.employee_id,
            self.employee.id,
        )

        self.assertEqual(
            event.processing_status,
            AttendanceEvent
            .ProcessingStatus
            .PROCESSED,
        )

        record = (
            AttendanceRecord.objects.get(
                employee=self.employee,
                attendance_date=occurred_at.date(),
            )
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.INCOMPLETE,
        )

    @patch.object(
        FA210Adapter,
        "connect",
    )
    @patch.object(
        FA210Adapter,
        "disconnect",
    )
    @patch.object(
        FA210Adapter,
        "get_attendance",
    )
    def test_date_filter(
        self,
        mock_get_attendance,
        mock_disconnect,
        mock_connect,
    ):

        self.create_mapping()

        first_day = datetime(
            2026,
            9,
            20,
            8,
            0,
            tzinfo=dt_timezone.utc,
        )

        second_day = datetime(
            2026,
            9,
            21,
            8,
            0,
            tzinfo=dt_timezone.utc,
        )

        mock_get_attendance.return_value = [
            self.create_record(
                uid=1,
                user_id="105",
                occurred_at=first_day,
            ),
            self.create_record(
                uid=2,
                user_id="105",
                occurred_at=second_day,
            ),
        ]

        adapter = FA210Adapter(
            device=self.device,
        )

        result = adapter.sync_attendance(
            start_date=second_day.date(),
            end_date=second_day.date(),
        )

        self.assertEqual(
            result["records_read"],
            2,
        )

        self.assertEqual(
            result["created"],
            1,
        )

        self.assertEqual(
            AttendanceEvent.objects.count(),
            1,
        )

        event = (
            AttendanceEvent.objects.get()
        )

        self.assertEqual(
            event.occurred_at.date(),
            second_day.date(),
        )

    @patch.object(
        FA210Adapter,
        "connect",
    )
    @patch.object(
        FA210Adapter,
        "disconnect",
    )
    @patch.object(
        FA210Adapter,
        "get_attendance",
    )
    def test_unknown_punch_creates_invalid_event_exception(
        self,
        mock_get_attendance,
        mock_disconnect,
        mock_connect,
    ):

        self.create_mapping()

        occurred_at = datetime(
            2026,
            9,
            21,
            8,
            0,
            tzinfo=dt_timezone.utc,
        )

        mock_get_attendance.return_value = [
            self.create_record(
                uid=1,
                user_id="105",
                occurred_at=occurred_at,
                punch=99,
            ),
        ]

        adapter = FA210Adapter(
            device=self.device,
        )

        result = adapter.sync_attendance()

        self.assertEqual(
            result["invalid"],
            1,
        )

        event = (
            AttendanceEvent.objects.get()
        )

        self.assertEqual(
            event.event_type,
            AttendanceEvent.EventType.UNKNOWN,
        )

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
                    .INVALID_EVENT
                ),
            ).exists()
        )

    @patch(
        "apps.attendance.integrations.fa210."
        "FA210Adapter.sync_attendance"
    )
    def test_run_sync_creates_success_log(
        self,
        mock_sync,
    ):

        mock_sync.return_value = {
            "records_read": 100,
            "records_in_range": 20,
            "created": 20,
            "duplicates": 0,
            "resolved_existing": 0,
            "unresolved": 0,
            "invalid": 0,
            "attendance_days_rebuilt": 10,
        }

        sync_log = (
            AttendanceSyncService.run_sync(
                device=self.device,
            )
        )

        self.assertEqual(
            sync_log.status,
            AttendanceSyncLog.Status.SUCCESS,
        )

        self.assertEqual(
            sync_log.records_read,
            100,
        )

        self.assertEqual(
            sync_log.records_in_range,
            20,
        )

        self.assertEqual(
            sync_log.created,
            20,
        )

        self.assertIsNotNone(
            sync_log.completed_at,
        )


    @patch(
        "apps.attendance.integrations.fa210."
        "FA210Adapter.sync_attendance"
    )
    def test_run_sync_creates_failed_log(
        self,
        mock_sync,
    ):

        mock_sync.side_effect = (
            ConnectionError(
                "FA210 connection failed."
            )
        )

        with self.assertRaises(
            ConnectionError
        ):

            AttendanceSyncService.run_sync(
                device=self.device,
            )

        sync_log = (
            AttendanceSyncLog.objects
            .get(
                device=self.device,
            )
        )

        self.assertEqual(
            sync_log.status,
            AttendanceSyncLog.Status.FAILED,
        )

        self.assertEqual(
            sync_log.error_message,
            "FA210 connection failed.",
        )

        self.assertIsNotNone(
            sync_log.completed_at,
        )