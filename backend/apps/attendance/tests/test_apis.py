from types import SimpleNamespace
from unittest.mock import patch
import uuid
from django.urls import reverse

from datetime import date, datetime

from django.utils import timezone

from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from apps.access.services import (
    AccessService,
    RoleService,
)

from apps.organization.models import (
    Organization,
)

from apps.employee.services import (
    EmployeeService,
)

from apps.attendance.models import (
    AttendanceDevice,
    AttendanceDeviceEmployee,
    AttendanceRecord,
    AttendanceEvent,
    AttendanceSyncLog,
)

from apps.attendance.services import (
    AttendanceDeviceService,
    AttendanceSyncService,
    AttendanceRecordService,
)


class AttendanceDeviceAPITests(
    APITestCase
):

    def setUp(self):

        # -----------------------------------
        # Organization
        # -----------------------------------

        self.organization = (
            Organization.objects.create(
                name="Test Company",
                legal_name="Test Company Limited",
            )
        )

        # -----------------------------------
        # User
        # -----------------------------------

        self.user = User.objects.create_user(
            email="admin@testcompany.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="Admin",
        )

        # -----------------------------------
        # Organization Admin Role
        # -----------------------------------

        self.role = (
            RoleService.provision_system_role(
                organization=self.organization,
                role_code="ORGANIZATION_ADMIN",
            )
        )

        # -----------------------------------
        # Organization Membership
        # -----------------------------------

        self.membership = (
            AccessService.assign_role(
                user=self.user,
                organization=self.organization,
                role=self.role,
            )
        )

        # -----------------------------------
        # Employee
        # -----------------------------------

        self.employee = (
            EmployeeService.create_employee(
                organization=self.organization,
                first_name="John",
                last_name="Doe",
                company_email="john@testcompany.com",
            )
        )

        # -----------------------------------
        # Attendance Device
        # -----------------------------------

        self.device = (
            AttendanceDeviceService.register_device(
                organization=self.organization,
                name="Main Entrance",
                vendor="Granding",
                model="FA210-Plus",
                serial_number="FA210-001",
                connection_type=(
                    AttendanceDevice
                    .ConnectionType
                    .NETWORK
                ),
                ip_address="192.168.1.50",
                port=4370,
            )
        )

        # -----------------------------------
        # Authenticate
        # -----------------------------------

        self.client.force_authenticate(
            user=self.user,
        )

    # =======================================
    # URL HELPERS
    # =======================================

    def device_users_url(self):
        return (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/devices/{self.device.id}/"
            f"users/"
        )

    def mappings_url(self):
        return (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/devices/{self.device.id}/"
            f"mappings/"
        )

    def mapping_detail_url(
        self,
        device_user_id,
    ):
        return (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/devices/{self.device.id}/"
            f"mappings/{device_user_id}/"
        )

    def attendance_records_url(self):
        return (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/records/"
        )

    def attendance_device_sync_url(self):
        return (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/devices/{self.device.id}/"
            f"sync/"
        )

    def attendance_record_reconcile_url(
        self,
        record_id,
    ):
        return (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/records/{record_id}/"
            f"reconcile/"
        )


    # =======================================
    # DEVICE SYNCHRONIZATION
    # =======================================

    @patch(#
        "apps.attendance.views.AttendanceSyncService.run_sync"
    )
    def test_device_sync_success(
        self,
        mock_run_sync,
    ):

        sync_log = AttendanceSyncLog.objects.create(
            organization=self.organization,
            device=self.device,
            trigger=AttendanceSyncLog.Trigger.API,
            status=AttendanceSyncLog.Status.SUCCESS,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 21),
            records_read=10,
            records_in_range=10,
            created=8,
            duplicates=2,
            resolved_existing=0,
            unresolved=0,
            invalid=0,
            attendance_days_rebuilt=5,
            completed_at=timezone.now(),
        )

        mock_run_sync.return_value = sync_log

        response = self.client.post(
            self.attendance_device_sync_url(),
            {
                "start_date": "2026-09-01",
                "end_date": "2026-09-21",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            str(sync_log.id),
        )

        self.assertEqual(
            response.data["organization_id"],
            str(self.organization.id),
        )

        self.assertEqual(
            response.data["device_id"],
            str(self.device.id),
        )

        self.assertEqual(
            response.data["device_name"],
            "Main Entrance",
        )

        self.assertEqual(
            response.data["trigger"],
            AttendanceSyncLog.Trigger.API,
        )

        self.assertEqual(
            response.data["status"],
            AttendanceSyncLog.Status.SUCCESS,
        )

        self.assertEqual(
            response.data["records_read"],
            10,
        )

        self.assertEqual(
            response.data["created"],
            8,
        )

        self.assertEqual(
            response.data["duplicates"],
            2,
        )

        mock_run_sync.assert_called_once_with(
            device=self.device,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 21),
            trigger=AttendanceSyncLog.Trigger.API,
        )

    def test_device_sync_rejects_invalid_date_range(self):

        response = self.client.post(
            self.attendance_device_sync_url(),
            {
                "start_date": "2026-09-21",
                "end_date": "2026-09-01",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "end_date",
            str(response.data),
        )

    def test_device_sync_rejects_device_from_another_organization(self):

        other_organization = Organization.objects.create(
            name="Other Organization",
            legal_name="Other Organization Limited",
        )

        # Give the authenticated user access to the other organization
        # so the permission layer allows the request to reach the view.
        other_role = RoleService.provision_system_role(
            organization=other_organization,
            role_code="ORGANIZATION_ADMIN",
        )

        AccessService.assign_role(
            user=self.user,
            organization=other_organization,
            role=other_role,
        )

        self.assertNotEqual(
            self.device.organization_id,
            other_organization.id,
        )

        self.assertEqual(
            self.device.organization_id,
            self.organization.id,
        )

        response = self.client.post(
            (
                f"/api/attendance/"
                f"organizations/{other_organization.id}/"
                f"attendance/devices/{self.device.id}/"
                f"sync/"
            ),
            {
                "start_date": "2026-09-01",
                "end_date": "2026-09-21",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
    # =======================================
    # GET DEVICE USERS
    # =======================================

    @patch(
        "apps.attendance.services."
        "AttendanceDeviceService.get_device_users"
    )
    def test_list_device_users(
        self,
        mock_get_device_users,
    ):

        mock_get_device_users.return_value = [
            SimpleNamespace(
                uid=16,
                user_id="23",
                name="Olumide",
                privilege=0,
                card=0,
            ),
            SimpleNamespace(
                uid=17,
                user_id="24",
                name="Celine Emmanuel",
                privilege=0,
                card=0,
            ),
        ]

        response = self.client.get(
            self.device_users_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            2,
        )

        self.assertEqual(
            response.data[0]["user_id"],
            "23",
        )

        self.assertEqual(
            response.data[0]["name"],
            "Olumide",
        )

        self.assertFalse(
            response.data[0]["mapped"],
        )

        mock_get_device_users.assert_called_once_with(
            device=self.device,
        )

    # =======================================
    # GET DEVICE USERS WITH MAPPING
    # =======================================

    @patch(
        "apps.attendance.services."
        "AttendanceDeviceService.get_device_users"
    )
    def test_device_user_shows_employee_mapping(
        self,
        mock_get_device_users,
    ):

        mock_get_device_users.return_value = [
            SimpleNamespace(
                uid=16,
                user_id="23",
                name="Olumide",
                privilege=0,
                card=0,
            ),
        ]

        AttendanceDeviceService.map_employee(
            device=self.device,
            employee=self.employee,
            device_user_id="23",
            display_name="Olumide",
        )

        response = self.client.get(
            self.device_users_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertTrue(
            response.data[0]["mapped"],
        )

        self.assertEqual(
            response.data[0]["employee_id"],
            str(self.employee.id),
        )

        self.assertEqual(
            response.data[0]["employee_number"],
            self.employee.employee_number,
        )

        self.assertEqual(
            response.data[0]["employee_name"],
            "John Doe",
        )

    # =======================================
    # GET MAPPINGS
    # =======================================

    def test_list_employee_mappings(
        self,
    ):

        AttendanceDeviceService.map_employee(
            device=self.device,
            employee=self.employee,
            device_user_id="23",
            display_name="John Doe",
        )

        response = self.client.get(
            self.mappings_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["device_user_id"],
            "23",
        )

        self.assertEqual(
            response.data[0]["employee"],
            str(self.employee.id),
        )

        self.assertTrue(
            response.data[0]["is_active"],
        )

    # =======================================
    # CREATE MAPPING
    # =======================================

    def test_create_employee_mapping(
        self,
    ):

        payload = {
            "device_user_id": "23",
            "employee_id": str(
                self.employee.id
            ),
            "display_name": "John Doe",
        }

        response = self.client.post(
            self.mappings_url(),
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["device_user_id"],
            "23",
        )

        self.assertEqual(
            response.data["employee"],
            str(self.employee.id),
        )

        self.assertEqual(
            response.data["display_name"],
            "John Doe",
        )

        self.assertTrue(
            response.data["is_active"],
        )

        self.assertTrue(
            AttendanceDeviceEmployee.objects.filter(
                device=self.device,
                employee=self.employee,
                device_user_id="23",
            ).exists()
        )

    # =======================================
    # CREATE MAPPING - DUPLICATE USER
    # =======================================

    def test_create_duplicate_device_user_mapping_is_rejected(
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

        AttendanceDeviceService.map_employee(
            device=self.device,
            employee=self.employee,
            device_user_id="23",
        )

        payload = {
            "device_user_id": "23",
            "employee_id": str(
                employee_two.id
            ),
        }

        response = self.client.post(
            self.mappings_url(),
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # =======================================
    # CREATE MAPPING - UNKNOWN EMPLOYEE
    # =======================================

    def test_create_mapping_with_unknown_employee(
        self,
    ):

        payload = {
            "device_user_id": "23",
            "employee_id": str(
                uuid.uuid4()
            ),
        }

        response = self.client.post(
            self.mappings_url(),
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # =======================================
    # GET MAPPING DETAIL
    # =======================================

    def test_get_mapping_detail(
        self,
    ):

        AttendanceDeviceService.map_employee(
            device=self.device,
            employee=self.employee,
            device_user_id="23",
            display_name="John Doe",
        )

        response = self.client.get(
            self.mapping_detail_url("23")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["device_user_id"],
            "23",
        )

        self.assertEqual(
            response.data["employee"],
            str(self.employee.id),
        )

    # =======================================
    # GET NONEXISTENT MAPPING
    # =======================================

    def test_get_nonexistent_mapping(
        self,
    ):

        response = self.client.get(
            self.mapping_detail_url("999")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # =======================================
    # REMAP EMPLOYEE
    # =======================================

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

        AttendanceDeviceService.map_employee(
            device=self.device,
            employee=self.employee,
            device_user_id="23",
            display_name="John Doe",
        )

        payload = {
            "employee_id": str(
                employee_two.id
            ),
            "display_name": "Jane Doe",
        }

        response = self.client.patch(
            self.mapping_detail_url("23"),
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["device_user_id"],
            "23",
        )

        self.assertEqual(
            response.data["employee"],
            str(employee_two.id),
        )

        self.assertEqual(
            response.data["employee_name"],
            "Jane Doe",
        )

    # =======================================
    # DELETE MAPPING
    # =======================================

    def test_delete_mapping(
        self,
    ):

        AttendanceDeviceService.map_employee(
            device=self.device,
            employee=self.employee,
            device_user_id="23",
        )

        response = self.client.delete(
            self.mapping_detail_url("23")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        mapping = (
            AttendanceDeviceEmployee.objects.get(
                device=self.device,
                device_user_id="23",
            )
        )

        self.assertFalse(
            mapping.is_active,
        )

    # =======================================
    # DEVICE ORGANIZATION ISOLATION
    # =======================================

    def test_device_cannot_be_accessed_through_another_organization(
        self,
    ):

        another_organization = (
            Organization.objects.create(
                name="Another Company",
                legal_name="Another Company Limited",
            )
        )

        another_role = (
            RoleService.provision_system_role(
                organization=another_organization,
                role_code="ORGANIZATION_ADMIN",
            )
        )

        AccessService.assign_role(
            user=self.user,
            organization=another_organization,
            role=another_role,
        )

        response = self.client.get(
            (
                f"/api/attendance/"
                f"organizations/{another_organization.id}/"
                f"attendance/devices/{self.device.id}/"
                f"mappings/"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # =======================================
    # GET ATTENDANCE RECORDS
    # =======================================

    def test_list_attendance_records(
        self,
    ):

        AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date="2026-09-21",
            status=AttendanceRecord.Status.PRESENT,
            first_check_in_at="2026-09-21T08:00:00Z",
            last_check_out_at="2026-09-21T17:00:00Z",
            checkout_source=(
                AttendanceRecord.CheckoutSource.DEVICE
            ),
            worked_minutes=540,
            late_minutes=0,
            early_departure_minutes=0,
        )

        response = self.client.get(
            self.attendance_records_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        record = response.data[0]

        self.assertEqual(
            record["employee_id"],
            str(self.employee.id),
        )

        self.assertEqual(
            record["employee_number"],
            self.employee.employee_number,
        )

        self.assertEqual(
            record["employee_name"],
            "John Doe",
        )

        self.assertEqual(
            record["attendance_date"],
            "2026-09-21",
        )

        self.assertEqual(
            record["status"],
            AttendanceRecord.Status.PRESENT,
        )

        self.assertEqual(
            record["checkout_source"],
            AttendanceRecord.CheckoutSource.DEVICE,
        )

        self.assertEqual(
            record["worked_minutes"],
            540,
        )

    # =======================================
    # GET ATTENDANCE RECORDS
    # =======================================

    def test_list_attendance_records(
        self,
    ):

        AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date="2026-09-21",
            status=AttendanceRecord.Status.PRESENT,
            first_check_in_at="2026-09-21T08:00:00Z",
            last_check_out_at="2026-09-21T17:00:00Z",
            checkout_source=(
                AttendanceRecord.CheckoutSource.DEVICE
            ),
            worked_minutes=540,
            late_minutes=0,
            early_departure_minutes=0,
        )

        response = self.client.get(
            self.attendance_records_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            len(response.data["results"]),
            1,
        )

        record = response.data["results"][0]

        self.assertEqual(
            record["employee_id"],
            str(self.employee.id),
        )

        self.assertEqual(
            record["employee_number"],
            self.employee.employee_number,
        )

        self.assertEqual(
            record["employee_name"],
            "John Doe",
        )

        self.assertEqual(
            record["attendance_date"],
            "2026-09-21",
        )

        self.assertEqual(
            record["status"],
            AttendanceRecord.Status.PRESENT,
        )

        self.assertEqual(
            record["checkout_source"],
            AttendanceRecord.CheckoutSource.DEVICE,
        )

        self.assertEqual(
            record["worked_minutes"],
            540,
        )

    def test_filter_attendance_records_by_employee(
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

        AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date="2026-09-21",
            status=AttendanceRecord.Status.PRESENT,
        )

        AttendanceRecord.objects.create(
            organization=self.organization,
            employee=employee_two,
            attendance_date="2026-09-21",
            status=AttendanceRecord.Status.PRESENT,
        )

        response = self.client.get(
            self.attendance_records_url(),
            {
                "employee_id": str(
                    self.employee.id
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            len(response.data["results"]),
            1,
        )

        self.assertEqual(
            response.data["results"][0]["employee_id"],
            str(self.employee.id),
        )

    def test_filter_attendance_records_by_date_range(
        self,
    ):

        AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date="2026-09-01",
            status=AttendanceRecord.Status.PRESENT,
        )

        AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date="2026-09-15",
            status=AttendanceRecord.Status.PRESENT,
        )

        AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date="2026-09-30",
            status=AttendanceRecord.Status.PRESENT,
        )

        response = self.client.get(
            self.attendance_records_url(),
            {
                "date_from": "2026-09-10",
                "date_to": "2026-09-20",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            len(response.data["results"]),
            1,
        )

        self.assertEqual(
            response.data["results"][0]["attendance_date"],
            "2026-09-15",
        )

    def test_filter_attendance_records_by_status(
        self,
    ):

        AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date="2026-09-21",
            status=AttendanceRecord.Status.PRESENT,
        )

        AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date="2026-09-22",
            status=AttendanceRecord.Status.INCOMPLETE,
        )

        response = self.client.get(
            self.attendance_records_url(),
            {
                "status": (
                    AttendanceRecord.Status.INCOMPLETE
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            len(response.data["results"]),
            1,
        )

        self.assertEqual(
            response.data["results"][0]["status"],
            AttendanceRecord.Status.INCOMPLETE,
        )

    # =======================================
    # ATTENDANCE RECORD PAGINATION
    # =======================================

    def test_attendance_records_are_paginated(
        self,
    ):

        for day in range(1, 26):
            AttendanceRecord.objects.create(
                organization=self.organization,
                employee=self.employee,
                attendance_date=(
                    f"2026-09-{day:02d}"
                ),
                status=AttendanceRecord.Status.PRESENT,
            )

        response = self.client.get(
            self.attendance_records_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            25,
        )

        self.assertEqual(
            len(response.data["results"]),
            20,
        )

        self.assertIsNotNone(
            response.data["next"],
        )

        self.assertIsNone(
            response.data["previous"],
        )

        response = self.client.get(
            self.attendance_records_url(),
            {
                "page": 2,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            25,
        )

        self.assertEqual(
            len(response.data["results"]),
            5,
        )

        self.assertIsNone(
            response.data["next"],
        )

        self.assertIsNotNone(
            response.data["previous"],
        )

    def test_retrieve_attendance_record(self):
        attendance_record = AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date=date(2026, 9, 15),
            status=AttendanceRecord.Status.PRESENT,
            first_check_in_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 0)
            ),
            last_check_out_at=timezone.make_aware(
                datetime(2026, 9, 15, 17, 0)
            ),
            checkout_source=AttendanceRecord.CheckoutSource.DEVICE,
            worked_minutes=540,
        )

        url = (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/records/{attendance_record.id}/"
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["id"],
            str(attendance_record.id),
        )
        self.assertEqual(
            response.data["employee_id"],
            str(self.employee.id),
        )
        self.assertEqual(
            response.data["employee_number"],
            self.employee.employee_number,
        )
        self.assertEqual(
            response.data["attendance_date"],
            "2026-09-15",
        )
        self.assertEqual(
            response.data["status"],
            AttendanceRecord.Status.PRESENT,
        )
        self.assertEqual(
            response.data["worked_minutes"],
            540,
        )

    def test_attendance_record_detail_isolated_by_organization(self):
        attendance_record = AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date=date(2026, 9, 15),
            status=AttendanceRecord.Status.PRESENT,
        )

        other_organization = Organization.objects.create(
            name="Other Organization",
        )

        admin_role = RoleService.provision_system_role(
            organization=other_organization,
            role_code="ORGANIZATION_ADMIN",
        )

        AccessService.assign_role(
            user=self.user,
            organization=other_organization,
            role=admin_role,
        )

        url = (
            f"/api/attendance/"
            f"organizations/{other_organization.id}/"
            f"attendance/records/{attendance_record.id}/"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_retrieve_nonexistent_attendance_record(self):
        url = (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/records/"
            f"00000000-0000-0000-0000-000000000000/"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_list_attendance_events(self):
        event = AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 0)
            ),
            device_user_id="1001",
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        url = (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/events/"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        result = response.data["results"][0]

        self.assertEqual(
            result["id"],
            str(event.id),
        )

        self.assertEqual(
            result["employee_id"],
            str(self.employee.id),
        )

        self.assertEqual(
            result["employee_number"],
            self.employee.employee_number,
        )

        self.assertEqual(
            result["event_type"],
            AttendanceEvent.EventType.CHECK_IN,
        )

        self.assertEqual(
            result["source"],
            AttendanceEvent.Source.DEVICE,
        )

        self.assertEqual(
            result["device_user_id"],
            "1001",
        )

    def test_attendance_events_are_isolated_by_organization(self):
        event = AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 0)
            ),
            device_user_id="1001",
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        other_organization = Organization.objects.create(
            name="Other Organization",
        )

        admin_role = RoleService.provision_system_role(
            organization=other_organization,
            role_code="ORGANIZATION_ADMIN",
        )

        AccessService.assign_role(
            user=self.user,
            organization=other_organization,
            role=admin_role,
        )

        url = (
            f"/api/attendance/"
            f"organizations/{other_organization.id}/"
            f"attendance/events/"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            0,
        )

    def test_filter_attendance_events_by_employee(self):
        other_employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="Fortune",
            last_name="Maduka",
            employee_number="EMP-002",
        )

        first_event = AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 0)
            ),
            device_user_id="1001",
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        AttendanceEvent.objects.create(
            organization=self.organization,
            employee=other_employee,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 5)
            ),
            device_user_id="1002",
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        url = (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/events/"
            f"?employee_id={self.employee.id}"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        result = response.data["results"][0]

        self.assertEqual(
            result["id"],
            str(first_event.id),
        )

        self.assertEqual(
            result["employee_id"],
            str(self.employee.id),
        )

    def test_filter_attendance_events_by_device(self):
        other_device = AttendanceDeviceService.register_device(
            organization=self.organization,
            name="Second Attendance Device",
        )

        first_event = AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            device=self.device,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 0)
            ),
            device_user_id="1001",
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            device=other_device,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 5)
            ),
            device_user_id="1001",
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        url = (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/events/"
            f"?device_id={self.device.id}"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        result = response.data["results"][0]

        self.assertEqual(
            result["id"],
            str(first_event.id),
        )

        self.assertEqual(
            result["device_id"],
            str(self.device.id),
        )

    def test_filter_attendance_events_by_event_type(self):
        check_in_event = AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            device=self.device,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 0)
            ),
            device_user_id="1001",
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            device=self.device,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_OUT,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 15, 17, 0)
            ),
            device_user_id="1001",
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        url = (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/events/"
            f"?event_type={AttendanceEvent.EventType.CHECK_IN}"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        result = response.data["results"][0]

        self.assertEqual(
            result["id"],
            str(check_in_event.id),
        )

        self.assertEqual(
            result["event_type"],
            AttendanceEvent.EventType.CHECK_IN,
        )

    def test_filter_attendance_events_by_source(self):
        device_event = AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            device=self.device,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 0)
            ),
            device_user_id="1001",
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            source=AttendanceEvent.Source.WEB,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 5)
            ),
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        url = (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/events/"
            f"?source={AttendanceEvent.Source.DEVICE}"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        result = response.data["results"][0]

        self.assertEqual(
            result["id"],
            str(device_event.id),
        )

        self.assertEqual(
            result["source"],
            AttendanceEvent.Source.DEVICE,
        )

    def test_filter_attendance_events_by_source(self):
        device_event = AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            device=self.device,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 0)
            ),
            device_user_id="1001",
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            source=AttendanceEvent.Source.WEB,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 5)
            ),
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        url = (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/events/"
            f"?source={AttendanceEvent.Source.DEVICE}"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        result = response.data["results"][0]

        self.assertEqual(
            result["id"],
            str(device_event.id),
        )

        self.assertEqual(
            result["source"],
            AttendanceEvent.Source.DEVICE,
        )

    def test_filter_attendance_events_by_date_range(self):
        first_event = AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            device=self.device,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 1, 8, 0)
            ),
            device_user_id="1001",
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        matching_event = AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            device=self.device,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 0)
            ),
            device_user_id="1001",
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        last_event = AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            device=self.device,
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.make_aware(
                datetime(2026, 9, 30, 8, 0)
            ),
            device_user_id="1001",
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        url = (
            f"/api/attendance/"
            f"organizations/{self.organization.id}/"
            f"attendance/events/"
            f"?date_from=2026-09-10"
            f"&date_to=2026-09-20"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        result = response.data["results"][0]

        self.assertEqual(
            result["id"],
            str(matching_event.id),
        )

        self.assertNotEqual(
            result["id"],
            str(first_event.id),
        )

        self.assertNotEqual(
            result["id"],
            str(last_event.id),
        )

    def test_retrieve_attendance_event(self):
        event = AttendanceEvent.objects.create(
            organization=self.organization,
            employee=self.employee,
            device=self.device,
            device_user_id="1001",
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.now(),
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        response = self.client.get(
            reverse(
                "attendance-event-detail",
                kwargs={
                    "organization_id": self.organization.id,
                    "event_id": event.id,
                },
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(event.id))
        self.assertEqual(response.data["device_user_id"], "1001")
        self.assertEqual(
            response.data["event_type"],
            AttendanceEvent.EventType.CHECK_IN,
        )

    def test_attendance_event_detail_isolated_by_organization(self):
        other_organization = Organization.objects.create(
            name="Other Organization",
        )

        other_admin = User.objects.create_user(
            email="other-admin@example.com",
            password="test-password",
        )

        admin_role = RoleService.provision_system_role(
            organization=other_organization,
            role_code="ORGANIZATION_ADMIN",
        )

        AccessService.assign_role(
            user=other_admin,
            organization=other_organization,
            role=admin_role,
        )

        other_employee = EmployeeService.create_employee(
            organization=other_organization,
            first_name="Maduka",
            last_name="Fortune",
        )

        other_device = self.device

        event = AttendanceEvent.objects.create(
            organization=other_organization,
            employee=other_employee,
            device=other_device,
            device_user_id="2001",
            source=AttendanceEvent.Source.DEVICE,
            event_type=AttendanceEvent.EventType.CHECK_IN,
            occurred_at=timezone.now(),
            processing_status=AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse(
                "attendance-event-detail",
                kwargs={
                    "organization_id": self.organization.id,
                    "event_id": event.id,
                },
            )
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manual_check_in_creates_processed_event_and_record(self):
        url = reverse(
            "attendance-manual-check-in",
            kwargs={
                "organization_id": self.organization.id,
            },
        )

        occurred_at = timezone.now()

        response = self.client.post(
            url,
            {
                "employee_id": str(self.employee.id),
                "occurred_at": occurred_at.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        event = AttendanceEvent.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            event.organization,
            self.organization,
        )

        self.assertEqual(
            event.employee,
            self.employee,
        )

        self.assertEqual(
            event.source,
            AttendanceEvent.Source.MANUAL,
        )

        self.assertEqual(
            event.event_type,
            AttendanceEvent.EventType.CHECK_IN,
        )

        self.assertEqual(
            event.processing_status,
            AttendanceEvent.ProcessingStatus.PROCESSED,
        )

        record = AttendanceRecord.objects.get(
            employee=self.employee,
            attendance_date=occurred_at.date(),
        )

        self.assertEqual(
            record.first_check_in_at,
            event.occurred_at,
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.INCOMPLETE,
        )


    def test_manual_check_in_without_occurred_at_uses_current_time(self):
        url = reverse(
            "attendance-manual-check-in",
            kwargs={
                "organization_id": self.organization.id,
            },
        )

        before = timezone.now()

        response = self.client.post(
            url,
            {
                "employee_id": str(self.employee.id),
            },
            format="json",
        )

        after = timezone.now()

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        event = AttendanceEvent.objects.get(
            id=response.data["id"]
        )

        self.assertGreaterEqual(
            event.occurred_at,
            before,
        )

        self.assertLessEqual(
            event.occurred_at,
            after,
        )


    def test_manual_check_in_rejects_inactive_employee(self):
        self.employee.is_active = False
        self.employee.save(
            update_fields=["is_active"]
        )

        url = reverse(
            "attendance-manual-check-in",
            kwargs={
                "organization_id": self.organization.id,
            },
        )

        response = self.client.post(
            url,
            {
                "employee_id": str(self.employee.id),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "inactive employee",
            str(response.data).lower(),
        )


    def test_manual_check_in_rejects_employee_from_another_organization(
        self,
    ):
        other_organization = Organization.objects.create(
            name="Other Organization",
        )

        other_user = User.objects.create_user(
            email="other@example.com",
            password="TestPassword123!",
        )

        role = RoleService.provision_system_role(
            organization=other_organization,
            role_code="ORGANIZATION_ADMIN",
        )

        AccessService.assign_role(
            user=other_user,
            organization=other_organization,
            role=role,
        )

        other_employee = EmployeeService.create_employee(
            organization=other_organization,
            employee_number="EMP-OTHER",
            first_name="Other",
            last_name="Employee",
        )

        url = reverse(
            "attendance-manual-check-in",
            kwargs={
                "organization_id": self.organization.id,
            },
        )

        response = self.client.post(
            url,
            {
                "employee_id": str(other_employee.id),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_manual_check_in_requires_manual_attendance_permission(self):
        employee_user = User.objects.create_user(
            email="employee@example.com",
            password="TestPassword123!",
        )

        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="EMPLOYEE",
        )

        AccessService.assign_role(
            user=employee_user,
            organization=self.organization,
            role=role,
        )

        self.client.force_authenticate(
            user=employee_user
        )

        url = reverse(
            "attendance-manual-check-in",
            kwargs={
                "organization_id": self.organization.id,
            },
        )

        response = self.client.post(
            url,
            {
                "employee_id": str(self.employee.id),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    @patch(
        "apps.attendance.views.AttendanceRecordService."
        "reconcile_open_attendance_record"
    )
    def test_reconcile_attendance_record_success(
        self,
        mock_reconcile,
    ):
        attendance_record = (
            AttendanceRecord.objects.create(
                organization=self.organization,
                employee=self.employee,
                attendance_date=date(
                    2026,
                    9,
                    15,
                ),
                status=(
                    AttendanceRecord.Status.INCOMPLETE
                ),
                first_check_in_at=timezone.make_aware(
                    datetime(
                        2026,
                        9,
                        15,
                        8,
                        0,
                    )
                ),
            )
        )

        attendance_record.last_check_out_at = (
            timezone.make_aware(
                datetime(
                    2026,
                    9,
                    15,
                    23,
                    0,
                )
            )
        )

        attendance_record.checkout_source = (
            AttendanceRecord.CheckoutSource.SYSTEM
        )

        attendance_record.status = (
            AttendanceRecord.Status.PRESENT
        )

        attendance_record.worked_minutes = 900

        attendance_record.save()

        mock_reconcile.return_value = (
            attendance_record
        )

        response = self.client.post(
            self.attendance_record_reconcile_url(
                attendance_record.id
            ),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            str(attendance_record.id),
        )

        self.assertEqual(
            response.data["employee_id"],
            str(self.employee.id),
        )

        self.assertEqual(
            response.data["employee_number"],
            self.employee.employee_number,
        )

        self.assertEqual(
            response.data["attendance_date"],
            "2026-09-15",
        )

        self.assertEqual(
            response.data["status"],
            AttendanceRecord.Status.PRESENT,
        )

        self.assertEqual(
            response.data["checkout_source"],
            AttendanceRecord.CheckoutSource.SYSTEM,
        )

        self.assertEqual(
            response.data["worked_minutes"],
            900,
        )

        mock_reconcile.assert_called_once()

        called_record = (
            mock_reconcile.call_args.kwargs["record"]
        )

        self.assertEqual(
            called_record.id,
            attendance_record.id,
        )

    def test_reconcile_attendance_record_cross_organization_returns_404(self):
        other_organization = Organization.objects.create(
            name="Other Company",
        )

        other_employee = EmployeeService.create_employee(
            organization=other_organization,
            first_name="Jane",
            last_name="Smith",
        )

        attendance_record = AttendanceRecord.objects.create(
            organization=other_organization,
            employee=other_employee,
            attendance_date=date(2026, 9, 15),
            status=AttendanceRecord.Status.INCOMPLETE,
            first_check_in_at=timezone.make_aware(
                datetime(2026, 9, 15, 8, 0)
            ),
        )

        response = self.client.post(
            self.attendance_record_reconcile_url(attendance_record.id),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


    def test_reconcile_attendance_record_not_found_returns_404(self):
        record_id = uuid.uuid4()

        response = self.client.post(
            self.attendance_record_reconcile_url(record_id),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


    @patch(
        "apps.attendance.views.AttendanceRecordService."
        "reconcile_open_attendance_record"
    )
    def test_reconcile_attendance_record_not_eligible_returns_400(
        self,
        mock_reconcile,
    ):
        attendance_record = AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date=date(2026, 9, 16),
            status=AttendanceRecord.Status.PRESENT,
            first_check_in_at=timezone.make_aware(
                datetime(2026, 9, 16, 8, 0)
            ),
            last_check_out_at=timezone.make_aware(
                datetime(2026, 9, 16, 17, 0)
            ),
            checkout_source=AttendanceRecord.CheckoutSource.DEVICE,
            worked_minutes=540,
        )

        mock_reconcile.return_value = None

        response = self.client.post(
            self.attendance_record_reconcile_url(attendance_record.id),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data[0],
            "Attendance record is not eligible for reconciliation.",
        )

        mock_reconcile.assert_called_once()

        called_record = mock_reconcile.call_args.kwargs["record"]

        self.assertEqual(
            called_record.id,
            attendance_record.id,
        )

    @patch(
        "apps.attendance.views.AttendanceRecordService."
        "reconcile_open_attendance_record"
    )
    def test_reconcile_attendance_record_passes_scoped_record_to_service(
        self,
        mock_reconcile,
    ):
        attendance_record = AttendanceRecord.objects.create(
            organization=self.organization,
            employee=self.employee,
            attendance_date=date(2026, 9, 17),
            status=AttendanceRecord.Status.INCOMPLETE,
            first_check_in_at=timezone.make_aware(
                datetime(2026, 9, 17, 8, 0)
            ),
        )

        mock_reconcile.return_value = attendance_record

        response = self.client.post(
            self.attendance_record_reconcile_url(attendance_record.id),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        mock_reconcile.assert_called_once()

        called_record = mock_reconcile.call_args.kwargs["record"]

        self.assertEqual(
            called_record.id,
            attendance_record.id,
        )

        self.assertEqual(
            called_record.organization_id,
            self.organization.id,
        )

        self.assertEqual(
            called_record.employee_id,
            self.employee.id,
        )