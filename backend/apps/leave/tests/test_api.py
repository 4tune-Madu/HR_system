from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from apps.access.services import (
    AccessService,
    RoleService,
)

from apps.employee.services import (
    EmployeeService,
)

from apps.leave.models import (
    LeaveBalance,
    LeaveRequest,
    WorkSchedule,
    PublicHoliday,
    LeaveBalanceAdjustment,
)

from apps.leave.services import (
    LeaveBalanceService,
    LeaveRequestService,
    LeaveTypeService,
    LeavePolicyService,
    EmployeeWorkScheduleService,
    LeaveBalanceAdjustmentService,
    LeaveAccrualService,
)

from apps.organization.models import (
    Organization,
)
from decimal import Decimal
from datetime import date
from apps.access.models import(
    OrganizationMembership,
)

User = get_user_model()


class LeaveRequestAPITests(APITestCase):

    def setUp(self):

        # -----------------------------------
        # Organization
        # -----------------------------------

        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
        )

        # -----------------------------------
        # Admin / Reviewer
        # -----------------------------------

        self.admin_user = User.objects.create_user(
            email="admin@testcompany.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="Admin",
        )

        self.admin_role = (
            RoleService.provision_system_role(
                organization=self.organization,
                role_code="ORGANIZATION_ADMIN",
            )
        )

        AccessService.assign_role(
            user=self.admin_user,
            organization=self.organization,
            role=self.admin_role,
        )

        # -----------------------------------
        # Employee User
        # -----------------------------------

        self.employee_user = User.objects.create_user(
            email="employee@testcompany.com",
            password="TestPassword123!",
            first_name="John",
            last_name="Doe",
        )

        self.employee_role = (
            RoleService.provision_system_role(
                organization=self.organization,
                role_code="EMPLOYEE",
            )
        )

        AccessService.assign_role(
            user=self.employee_user,
            organization=self.organization,
            role=self.employee_role,
        )

        # -----------------------------------
        # Employee
        # -----------------------------------

        self.employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="employee@testcompany.com",
            user=self.employee_user,
        )

        # -----------------------------------
        # Leave Type
        # -----------------------------------

        self.leave_type = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        # -----------------------------------
        # Leave Policy
        # -----------------------------------

        self.leave_policy = (
            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=self.leave_type,
                days_per_year=20,
            )
        )

        # -----------------------------------
        # Leave Balance
        # -----------------------------------

        self.balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )
        )

        # -----------------------------------
        # URLs
        # -----------------------------------

        self.list_url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/requests/"
        )

        self.work_schedule = WorkSchedule.objects.create(
            organization=self.organization,
            code="MON_FRI",
            name="Monday to Friday",
            monday=True,
            tuesday=True,
            wednesday=True,
            thursday=True,
            friday=True,
            saturday=False,
            sunday=False,
            is_default=True,
            is_active=True,
        )

    # =================================================
    # Helpers
    # =================================================

    def request_detail_url(
        self,
        request_id,
    ):
        return (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/requests/{request_id}/"
        )

    def request_submit_url(
        self,
        request_id,
    ):
        return (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/requests/{request_id}/submit/"
        )

    def request_approve_url(
        self,
        request_id,
    ):
        return (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/requests/{request_id}/approve/"
        )

    def request_reject_url(
        self,
        request_id,
    ):
        return (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/requests/{request_id}/reject/"
        )

    def request_cancel_url(
        self,
        request_id,
    ):
        return (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/requests/{request_id}/cancel/"
        )

    def create_leave_request(self):
        return LeaveRequestService.create_request(
            employee=self.employee,
            leave_type=self.leave_type,
            organization=self.organization,
            start_date=date(2026, 8, 24),
            end_date=date(2026, 8, 28),
            reason="Annual vacation",
        )

    # =================================================
    # Create
    # =================================================

    def test_employee_can_create_leave_request(self):

        self.client.force_authenticate(
            user=self.employee_user,
        )

        response = self.client.post(
            self.list_url,
            {
                "leave_type": str(
                    self.leave_type.id
                ),
                "start_date": "2026-08-24",
                "end_date": "2026-08-28",
                "reason": "Annual vacation",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["status"],
            LeaveRequest.Status.DRAFT,
        )

        self.assertEqual(
            response.data["requested_days"],
            "5.00",
        )

    # =================================================
    # List
    # =================================================

    def test_admin_can_list_leave_requests(self):

        self.create_leave_request()

        self.client.force_authenticate(
            user=self.admin_user,
        )

        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    # =================================================
    # Detail
    # =================================================

    def test_admin_can_get_leave_request(self):

        leave_request = (
            self.create_leave_request()
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        response = self.client.get(
            self.request_detail_url(
                leave_request.id,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            str(response.data["id"]),
            str(leave_request.id),
        )

    # =================================================
    # Submit
    # =================================================

    def test_employee_can_submit_own_leave_request(
        self,
    ):

        leave_request = (
            self.create_leave_request()
        )

        self.client.force_authenticate(
            user=self.employee_user,
        )

        response = self.client.post(
            self.request_submit_url(
                leave_request.id,
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        leave_request.refresh_from_db()

        self.assertEqual(
            leave_request.status,
            LeaveRequest.Status.SUBMITTED,
        )

    # =================================================
    # Approve
    # =================================================

    def test_admin_can_approve_leave_request(
        self,
    ):

        leave_request = (
            self.create_leave_request()
        )

        LeaveRequestService.submit_request(
            leave_request=leave_request,
            organization=self.organization,
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        response = self.client.post(
            self.request_approve_url(
                leave_request.id,
            ),
            {
                "review_comment": "Approved.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        leave_request.refresh_from_db()
        self.balance.refresh_from_db()

        self.assertEqual(
            leave_request.status,
            LeaveRequest.Status.APPROVED,
        )

        self.assertEqual(
            self.balance.used_days,
            Decimal("5.00"),
        )

    # =================================================
    # Reject
    # =================================================

    def test_admin_can_reject_leave_request(
        self,
    ):

        leave_request = (
            self.create_leave_request()
        )

        LeaveRequestService.submit_request(
            leave_request=leave_request,
            organization=self.organization,
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        response = self.client.post(
            self.request_reject_url(
                leave_request.id,
            ),
            {
                "review_comment": "Not approved.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        leave_request.refresh_from_db()
        self.balance.refresh_from_db()

        self.assertEqual(
            leave_request.status,
            LeaveRequest.Status.REJECTED,
        )

        self.assertEqual(
            self.balance.used_days,
            Decimal("0"),
        )

    # =================================================
    # Cancel
    # =================================================

    def test_employee_can_cancel_own_leave_request(
        self,
    ):

        leave_request = (
            self.create_leave_request()
        )

        LeaveRequestService.submit_request(
            leave_request=leave_request,
            organization=self.organization,
        )

        self.client.force_authenticate(
            user=self.employee_user,
        )

        response = self.client.post(
            self.request_cancel_url(
                leave_request.id,
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        leave_request.refresh_from_db()

        self.assertEqual(
            leave_request.status,
            LeaveRequest.Status.CANCELLED,
        )

    # =================================================
    # Viewer / unauthorized approval
    # =================================================

    def test_employee_cannot_approve_leave_request(
        self,
    ):

        leave_request = (
            self.create_leave_request()
        )

        LeaveRequestService.submit_request(
            leave_request=leave_request,
            organization=self.organization,
        )

        self.client.force_authenticate(
            user=self.employee_user,
        )

        response = self.client.post(
            self.request_approve_url(
                leave_request.id,
            ),
            {
                "review_comment": "Trying to approve.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        leave_request.refresh_from_db()

        self.assertEqual(
            leave_request.status,
            LeaveRequest.Status.SUBMITTED,
        )

    # =================================================
    # Cannot submit another employee's request
    # =================================================

    def test_employee_cannot_submit_another_employees_request(
        self,
    ):

        leave_request = (
            self.create_leave_request()
        )

        another_user = User.objects.create_user(
            email="another@testcompany.com",
            password="TestPassword123!",
            first_name="Another",
            last_name="Employee",
        )

        another_role = (
            RoleService.provision_system_role(
                organization=self.organization,
                role_code="EMPLOYEE",
            )
        )

        AccessService.assign_role(
            user=another_user,
            organization=self.organization,
            role=another_role,
        )

        self.client.force_authenticate(
            user=another_user,
        )

        response = self.client.post(
            self.request_submit_url(
                leave_request.id,
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        leave_request.refresh_from_db()

        self.assertEqual(
            leave_request.status,
            LeaveRequest.Status.DRAFT,
        )

    def test_admin_cannot_approve_leave_request_with_insufficient_balance(
        self,
    ):
    
        leave_request = LeaveRequestService.create_request(
            employee=self.employee,
            leave_type=self.leave_type,
            organization=self.organization,
            start_date=date(2026, 8, 24),
            end_date=date(2026, 8, 28),
        )
    
        LeaveRequestService.submit_request(
            leave_request=leave_request,
            organization=self.organization,
        )
    
        # Only 2 days available, but request is 5 days.
        self.balance.entitlement_days = Decimal("2")
        self.balance.save(
            update_fields=[
                "entitlement_days",
                "updated_at",
            ]
        )
    
        self.client.force_authenticate(
            user=self.admin_user,
        )
    
        response = self.client.post(
            self.request_approve_url(
                leave_request.id,
            ),
            {
                "review_comment": "Approved.",
            },
            format="json",
        )
    
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
    
        self.assertIn(
            "not have enough",
            response.data["detail"].lower(),
        )
    
        leave_request.refresh_from_db()
        self.balance.refresh_from_db()
    
        self.assertEqual(
            leave_request.status,
            LeaveRequest.Status.SUBMITTED,
        )
    
        self.assertEqual(
            self.balance.used_days,
            Decimal("0"),
        )

    
    def test_cannot_access_leave_request_from_another_organization(
        self,
    ):
    
        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )
        
    
        another_user = User.objects.create_user(
            email="another.employee@testcompany.com",
            password="TestPassword123!",
            first_name="Another",
            last_name="Employee",
        )
    
        another_role = RoleService.provision_system_role(
            organization=another_organization,
            role_code="EMPLOYEE",
        )

        another_work_schedule = WorkSchedule.objects.create(
            organization=another_organization,
            code="MON_FRI",
            name="Monday to Friday",
            monday=True,
            tuesday=True,
            wednesday=True,
            thursday=True,
            friday=True,
            saturday=False,
            sunday=False,
            is_default=True,
            is_active=True,
        )
    
        AccessService.assign_role(
            user=another_user,
            organization=another_organization,
            role=another_role,
        )
    
        another_employee = EmployeeService.create_employee(
            organization=another_organization,
            first_name="Another",
            last_name="Employee",
            company_email="another.employee@testcompany.com",
            user=another_user,
        )
    
        another_leave_type = (
            LeaveTypeService.create_leave_type(
                organization=another_organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )
    
        LeavePolicyService.create_policy(
            organization=another_organization,
            leave_type=another_leave_type,
            days_per_year=20,
        )
    
        LeaveBalanceService.create_balance(
            employee=another_employee,
            leave_type=another_leave_type,
            year=2026,
            entitlement_days=Decimal("20"),
        )
    
        leave_request = LeaveRequestService.create_request(
            employee=another_employee,
            leave_type=another_leave_type,
            organization=another_organization,
            start_date=date(2026, 8, 24),
            end_date=date(2026, 8, 28),
        )
    
        self.client.force_authenticate(
            user=self.admin_user,
        )
    
        response = self.client.get(
            self.request_detail_url(
                leave_request.id,
            ),
        )
    
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
    
    def test_cannot_approve_draft_leave_request(
        self,
    ):
    
        leave_request = self.create_leave_request()
    
        self.client.force_authenticate(
            user=self.admin_user,
        )
    
        response = self.client.post(
            self.request_approve_url(
                leave_request.id,
            ),
            {
                "review_comment": "Approved.",
            },
            format="json",
        )
    
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
    
        leave_request.refresh_from_db()
    
        self.assertEqual(
            leave_request.status,
            LeaveRequest.Status.DRAFT,
        )
    
    def test_cannot_reject_draft_leave_request(
        self,
    ):
    
        leave_request = self.create_leave_request()
    
        self.client.force_authenticate(
            user=self.admin_user,
        )
    
        response = self.client.post(
            self.request_reject_url(
                leave_request.id,
            ),
            {
                "review_comment": "Rejected.",
            },
            format="json",
        )
    
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
    
        leave_request.refresh_from_db()
    
        self.assertEqual(
            leave_request.status,
            LeaveRequest.Status.DRAFT,
        )
    
    def test_employee_can_cancel_approved_leave(
        self,
    ):
    
        leave_request = self.create_leave_request()
    
        LeaveRequestService.submit_request(
            leave_request=leave_request,
            organization=self.organization,
        )
    
        self.client.force_authenticate(
            user=self.admin_user,
        )
    
        approval_response = self.client.post(
            self.request_approve_url(
                leave_request.id,
            ),
            {
                "review_comment": "Approved.",
            },
            format="json",
        )
    
        self.assertEqual(
            approval_response.status_code,
            status.HTTP_200_OK,
        )
    
        self.balance.refresh_from_db()
    
        self.assertEqual(
            self.balance.used_days,
            Decimal("5"),
        )
    
        self.client.force_authenticate(
            user=self.employee_user,
        )
    
        cancellation_response = self.client.post(
            self.request_cancel_url(
                leave_request.id,
            ),
            format="json",
        )
    
        self.assertEqual(
            cancellation_response.status_code,
            status.HTTP_200_OK,
        )
    
        leave_request.refresh_from_db()
        self.balance.refresh_from_db()
    
        self.assertEqual(
            leave_request.status,
            LeaveRequest.Status.CANCELLED,
        )
    
        self.assertEqual(
            self.balance.used_days,
            Decimal("0"),
        )
    
    def test_cannot_cancel_rejected_leave_request(
        self,
    ):
    
        leave_request = self.create_leave_request()
    
        LeaveRequestService.submit_request(
            leave_request=leave_request,
            organization=self.organization,
        )
    
        LeaveRequestService.reject_request(
            leave_request=leave_request,
            reviewed_by=self.admin_user,
            organization=self.organization,
            review_comment="Rejected.",
        )
    
        self.client.force_authenticate(
            user=self.employee_user,
        )
    
        response = self.client.post(
            self.request_cancel_url(
                leave_request.id,
            ),
            format="json",
        )
    
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
    
        leave_request.refresh_from_db()
    
        self.assertEqual(
            leave_request.status,
            LeaveRequest.Status.REJECTED,
        )



    def test_admin_can_create_leave_type(self):

        
        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/types/"
        )

        response = self.client.post(
            url,
            {
                "code": "SICK",
                "name": "Sick Leave",
                "description": "Medical leave.",
                "is_paid": True,
                "requires_approval": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["code"],
            "SICK",
        )

    def test_employee_cannot_manage_leave_type(self):

        self.client.force_authenticate(
            user=self.employee_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/types/"
        )

        response = self.client.post(
            url,
            {
                "code": "SICK",
                "name": "Sick Leave",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


    def test_admin_can_list_leave_balances(self):

        self.client.force_authenticate(
            user=self.admin_user,
        )

        response = self.client.get(
            (
                f"/api/leave/"
                f"organizations/{self.organization.id}/"
                f"leave/balances/"
            )
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
            response.data[0]["leave_type_name"],
            "Annual Leave",
        )


    def test_admin_can_list_employee_leave_balances(
        self,
    ):

        self.client.force_authenticate(
            user=self.admin_user,
        )

        response = self.client.get(
            (
                f"/api/leave/"
                f"organizations/{self.organization.id}/"
                f"employees/{self.employee.id}/"
                f"leave/balances/"
            )
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
            response.data[0]["remaining_days"],
            Decimal("20.00"),
        )


    def test_admin_can_get_leave_balance(self):

        self.client.force_authenticate(
            user=self.admin_user,
        )

        response = self.client.get(
            (
                f"/api/leave/"
                f"organizations/{self.organization.id}/"
                f"leave/balances/{self.balance.id}/"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["entitlement_days"],
            "20.00",
        )

        self.assertEqual(
            response.data["used_days"],
            "0.00",
        )

        self.assertEqual(
            response.data["remaining_days"],
            Decimal("20.00"),
        )

    def test_cannot_access_leave_balance_from_another_organization(
        self,
    ):

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_employee = EmployeeService.create_employee(
            organization=another_organization,
            first_name="Another",
            last_name="Employee",
            company_email="another.employee@testcompany.com",
        )

        another_leave_type = (
            LeaveTypeService.create_leave_type(
                organization=another_organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        LeavePolicyService.create_policy(
            organization=another_organization,
            leave_type=another_leave_type,
            days_per_year=20,
        )

        another_balance = (
            LeaveBalanceService.create_balance(
                employee=another_employee,
                leave_type=another_leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        response = self.client.get(
            (
                f"/api/leave/"
                f"organizations/{self.organization.id}/"
                f"leave/balances/{another_balance.id}/"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_balance_reflects_approved_leave(
        self,
    ):

        leave_request = (
            self.create_leave_request()
        )

        LeaveRequestService.submit_request(
            leave_request=leave_request,
            organization=self.organization,
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        response = self.client.post(
            self.request_approve_url(
                leave_request.id,
            ),
            {
                "review_comment": "Approved.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        balance_response = self.client.get(
            (
                f"/api/leave/"
                f"organizations/{self.organization.id}/"
                f"leave/balances/{self.balance.id}/"
            )
        )

        self.assertEqual(
            balance_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            balance_response.data["used_days"],
            "5.00",
        )

        self.assertEqual(
            balance_response.data["remaining_days"],
            Decimal("15.00"),
        )

    def test_leave_request_api_uses_working_days(
        self,
    ):

        self.client.force_authenticate(
            user=self.employee_user,
        )

        response = self.client.post(
            self.list_url,
            {
                "leave_type": str(
                    self.leave_type.id
                ),
                "start_date": "2026-08-28",
                "end_date": "2026-08-31",
                "reason": "Weekend-spanning leave",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["requested_days"],
            "2.00",
        )


    def test_admin_can_activate_public_holiday(
        self,
    ):
        holiday = PublicHoliday.objects.create(
            organization=self.organization,
            date=date(2026, 12, 25),
            name="Christmas Day",
            is_active=False,
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/holidays/{holiday.id}/"
            f"activate/"
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        holiday.refresh_from_db()

        self.assertTrue(
            holiday.is_active,
        )

        self.assertTrue(
            response.data["is_active"],
        )

    def test_cannot_activate_active_public_holiday(
        self,
    ):
        holiday = PublicHoliday.objects.create(
            organization=self.organization,
            date=date(2026, 12, 25),
            name="Christmas Day",
            is_active=True,
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/holidays/{holiday.id}/"
            f"activate/"
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        holiday.refresh_from_db()

        self.assertTrue(
            holiday.is_active,
        )

    def test_admin_can_deactivate_public_holiday(
        self,
    ):
        holiday = PublicHoliday.objects.create(
            organization=self.organization,
            date=date(2026, 12, 25),
            name="Christmas Day",
            is_active=True,
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/holidays/{holiday.id}/"
            f"deactivate/"
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        holiday.refresh_from_db()

        self.assertFalse(
            holiday.is_active,
        )

        self.assertFalse(
            response.data["is_active"],
        )

    def test_cannot_deactivate_inactive_public_holiday(
        self,
    ):
        holiday = PublicHoliday.objects.create(
            organization=self.organization,
            date=date(2026, 12, 25),
            name="Christmas Day",
            is_active=False,
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/holidays/{holiday.id}/"
            f"deactivate/"
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        holiday.refresh_from_db()

        self.assertFalse(
            holiday.is_active,
        )

    def test_employee_cannot_activate_public_holiday(
        self,
    ):
        holiday = PublicHoliday.objects.create(
            organization=self.organization,
            date=date(2026, 12, 25),
            name="Christmas Day",
            is_active=False,
        )

        self.client.force_authenticate(
            user=self.employee_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/holidays/{holiday.id}/"
            f"activate/"
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        holiday.refresh_from_db()

        self.assertFalse(
            holiday.is_active,
        )

    def test_employee_cannot_deactivate_public_holiday(
        self,
    ):
        holiday = PublicHoliday.objects.create(
            organization=self.organization,
            date=date(2026, 12, 25),
            name="Christmas Day",
            is_active=True,
        )

        self.client.force_authenticate(
            user=self.employee_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/holidays/{holiday.id}/"
            f"deactivate/"
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        holiday.refresh_from_db()

        self.assertTrue(
            holiday.is_active,
        )

    def test_cannot_activate_public_holiday_from_another_organization(
        self,
    ):
        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        holiday = PublicHoliday.objects.create(
            organization=another_organization,
            date=date(2026, 12, 25),
            name="Christmas Day",
            is_active=False,
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/holidays/{holiday.id}/"
            f"activate/"
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        holiday.refresh_from_db()

        self.assertFalse(
            holiday.is_active,
        )

    def test_cannot_deactivate_public_holiday_from_another_organization(
        self,
    ):
        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        holiday = PublicHoliday.objects.create(
            organization=another_organization,
            date=date(2026, 12, 25),
            name="Christmas Day",
            is_active=True,
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/holidays/{holiday.id}/"
            f"deactivate/"
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        holiday.refresh_from_db()

        self.assertTrue(
            holiday.is_active,
        )


    def test_admin_can_assign_employee_work_schedule(
        self,
    ):

        schedule = WorkSchedule.objects.create(
            organization=self.organization,
            code="MON_SAT",
            name="Monday to Saturday",
            saturday=True,
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"leave/work-schedules/"
        )

        response = self.client.post(
            url,
            {
                "work_schedule": str(
                    schedule.id,
                ),
                "effective_from": "2026-09-01",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            str(response.data["work_schedule"]),
            str(schedule.id),
        )

    def test_employee_cannot_assign_work_schedule(
        self,
    ):

        schedule = WorkSchedule.objects.create(
            organization=self.organization,
            code="MON_SAT",
            name="Monday to Saturday",
            saturday=True,
        )

        self.client.force_authenticate(
            user=self.employee_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"leave/work-schedules/"
        )

        response = self.client.post(
            url,
            {
                "work_schedule": str(
                    schedule.id,
                ),
                "effective_from": "2026-09-01",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_api_rejects_overlapping_employee_schedule(
        self,
    ):

        schedule_a = self.work_schedule

        schedule_b = WorkSchedule.objects.create(
            organization=self.organization,
            code="MON_SAT",
            name="Monday to Saturday",
            saturday=True,
        )

        EmployeeWorkScheduleService.assign_schedule(
            employee=self.employee,
            work_schedule=schedule_a,
            effective_from=date(2026, 1, 1),
            effective_to=date(2026, 6, 30),
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"leave/work-schedules/"
        )

        response = self.client.post(
            url,
            {
                "work_schedule": str(
                    schedule_b.id,
                ),
                "effective_from": "2026-06-01",
                "effective_to": "2026-12-31",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,4
        )

    def test_admin_can_create_employee_leave_entitlement(
        self,
    ):

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"leave/entitlements/"
        )

        response = self.client.post(
            url,
            {
                "leave_type": str(
                    self.leave_type.id,
                ),
                "year": 2026,
                "days": "25.00",
                "is_override": True,
                "reason": "Senior employee allowance.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["days"],
            "25.00",
        )

    def test_employee_cannot_manage_leave_entitlement(
        self,
    ):

        self.client.force_authenticate(
            user=self.employee_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"leave/entitlements/"
        )

        response = self.client.post(
            url,
            {
                "leave_type": str(
                    self.leave_type.id,
                ),
                "year": 2026,
                "days": "25.00",
                "is_override": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_cannot_create_entitlement_using_leave_type_from_another_organization(
        self,
    ):
        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_leave_type = (
            LeaveTypeService.create_leave_type(
                organization=another_organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"leave/entitlements/"
        )

        response = self.client.post(
            url,
            {
                "leave_type": str(
                    another_leave_type.id,
                ),
                "year": 2026,
                "days": "25.00",
                "is_override": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


    def test_admin_can_create_leave_balance_credit_adjustment(
        self,
    ):

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{self.balance.id}/"
            f"adjustments/"
        )

        response = self.client.post(
            url,
            {
                "amount": "3.00",
                "adjustment_type": "CREDIT",
                "reason": "Management granted additional leave.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["amount"],
            "3.00",
        )

        self.assertEqual(
            response.data["adjustment_type"],
            "CREDIT",
        )

        self.assertEqual(
            response.data["reason"],
            "Management granted additional leave.",
        )

        self.balance.refresh_from_db()

        self.assertEqual(
            self.balance.remaining_days,
            Decimal("23.00"),
        )


    def test_admin_can_create_leave_balance_debit_adjustment(
        self,
    ):

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{self.balance.id}/"
            f"adjustments/"
        )

        response = self.client.post(
            url,
            {
                "amount": "3.00",
                "adjustment_type": "DEBIT",
                "reason": "Leave balance correction.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["amount"],
            "3.00",
        )

        self.assertEqual(
            response.data["adjustment_type"],
            "DEBIT",
        )

        self.balance.refresh_from_db()

        self.assertEqual(
            self.balance.remaining_days,
            Decimal("17.00"),
        )

    def test_employee_cannot_create_leave_balance_adjustment(
        self,
    ):

        self.client.force_authenticate(
            user=self.employee_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{self.balance.id}/"
            f"adjustments/"
        )

        response = self.client.post(
            url,
            {
                "amount": "3.00",
                "adjustment_type": "CREDIT",
                "reason": "Give me extra leave.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            LeaveBalanceAdjustment.objects.count(),
            0,
        )

        self.balance.refresh_from_db()

        self.assertEqual(
            self.balance.remaining_days,
            Decimal("20.00"),
        )

    def test_admin_can_list_leave_balance_adjustments(
        self,
    ):

        LeaveBalanceAdjustmentService.create_adjustment(
            balance=self.balance,
            organization=self.organization,
            adjusted_by=self.admin_user,
            amount=Decimal("3.00"),
            adjustment_type=(
                LeaveBalanceAdjustment
                .AdjustmentType.CREDIT
            ),
            reason="Management granted additional leave.",
        )

        LeaveBalanceAdjustmentService.create_adjustment(
            balance=self.balance,
            organization=self.organization,
            adjusted_by=self.admin_user,
            amount=Decimal("1.00"),
            adjustment_type=(
                LeaveBalanceAdjustment
                .AdjustmentType.DEBIT
            ),
            reason="Correction.",
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{self.balance.id}/"
            f"adjustments/"
        )

        response = self.client.get(
            url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            2,
        )

    def test_employee_can_view_leave_balance_adjustments(
        self,
    ):

        LeaveBalanceAdjustmentService.create_adjustment(
            balance=self.balance,
            organization=self.organization,
            adjusted_by=self.admin_user,
            amount=Decimal("2.00"),
            adjustment_type=(
                LeaveBalanceAdjustment
                .AdjustmentType.CREDIT
            ),
            reason="Additional leave.",
        )

        self.client.force_authenticate(
            user=self.employee_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{self.balance.id}/"
            f"adjustments/"
        )

        response = self.client.get(
            url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_admin_cannot_debit_leave_balance_below_zero(
        self,
    ):

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{self.balance.id}/"
            f"adjustments/"
        )

        response = self.client.post(
            url,
            {
                "amount": "25.00",
                "adjustment_type": "DEBIT",
                "reason": "Invalid correction.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.balance.refresh_from_db()

        self.assertEqual(
            self.balance.remaining_days,
            Decimal("20.00"),
        )

        self.assertEqual(
            LeaveBalanceAdjustment.objects.count(),
            0,
        )

    def test_leave_balance_adjustment_requires_reason(
        self,
    ):

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{self.balance.id}/"
            f"adjustments/"
        )

        response = self.client.post(
            url,
            {
                "amount": "2.00",
                "adjustment_type": "CREDIT",
                "reason": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            LeaveBalanceAdjustment.objects.count(),
            0,
        )

    def test_leave_balance_adjustment_rejects_zero_amount(
        self,
    ):

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{self.balance.id}/"
            f"adjustments/"
        )

        response = self.client.post(
            url,
            {
                "amount": "0.00",
                "adjustment_type": "CREDIT",
                "reason": "Invalid adjustment.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_cannot_adjust_balance_from_another_organization(
        self,
    ):

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_employee = EmployeeService.create_employee(
            organization=another_organization,
            first_name="Another",
            last_name="Employee",
            company_email="another@testcompany.com",
        )

        another_leave_type = (
            LeaveTypeService.create_leave_type(
                organization=another_organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        LeavePolicyService.create_policy(
            organization=another_organization,
            leave_type=another_leave_type,
            days_per_year=20,
        )

        another_balance = (
            LeaveBalanceService.create_balance(
                employee=another_employee,
                leave_type=another_leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{another_balance.id}/"
            f"adjustments/"
        )

        response = self.client.post(
            url,
            {
                "amount": "2.00",
                "adjustment_type": "CREDIT",
                "reason": "Cross organization attempt.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(
            LeaveBalanceAdjustment.objects.count(),
            0,
        )


    def test_balance_api_reflects_adjustment(
        self,
    ):
    
        self.client.force_authenticate(
            user=self.admin_user,
        )
    
        adjustment_url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{self.balance.id}/"
            f"adjustments/"
        )
    
        adjustment_response = self.client.post(
            adjustment_url,
            {
                "amount": "4.00",
                "adjustment_type": "CREDIT",
                "reason": "Additional management leave.",
            },
            format="json",
        )
    
        self.assertEqual(
            adjustment_response.status_code,
            status.HTTP_201_CREATED,
        )
    
        balance_url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{self.balance.id}/"
        )
    
        balance_response = self.client.get(
            balance_url,
        )
    
        self.assertEqual(
            balance_response.status_code,
            status.HTTP_200_OK,
        )
    
        self.assertEqual(
            balance_response.data["remaining_days"],
            Decimal("24.00"),
        )



    def test_admin_can_list_leave_accruals(
        self,
    ):

        self.balance.entitlement_days = Decimal("24")
        self.balance.accrual_enabled = True
        self.balance.accrual_frequency = "MONTHLY"

        self.balance.save(
            update_fields=[
                "entitlement_days",
                "accrual_enabled",
                "accrual_frequency",
                "updated_at",
            ]
        )

        LeaveAccrualService.accrue_month(
            organization=self.organization,
            year=2026,
            month=1,
        )

        LeaveAccrualService.accrue_month(
            organization=self.organization,
            year=2026,
            month=2,
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{self.balance.id}/"
            f"accruals/"
        )

        response = self.client.get(
            url,
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
            response.data[0]["period_month"],
            2,
        )

        self.assertEqual(
            response.data[1]["period_month"],
            1,
        )

    def test_cannot_view_accruals_from_another_organization(
        self,
    ):

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_employee = (
            EmployeeService.create_employee(
                organization=another_organization,
                first_name="Another",
                last_name="Employee",
                company_email="another@testcompany.com",
            )
        )

        another_leave_type = (
            LeaveTypeService.create_leave_type(
                organization=another_organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        LeavePolicyService.create_policy(
            organization=another_organization,
            leave_type=another_leave_type,
            days_per_year=20,
        )
        
        another_balance = (
            LeaveBalanceService.create_balance(
                employee=another_employee,
                leave_type=another_leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{another_balance.id}/"
            f"accruals/"
        )

        response = self.client.get(
            url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_balance_api_shows_accrual_summary(
        self,
    ):

        self.balance.entitlement_days = Decimal("24")
        self.balance.accrual_enabled = True
        self.balance.accrual_frequency = "MONTHLY"

        self.balance.save(
            update_fields=[
                "entitlement_days",
                "accrual_enabled",
                "accrual_frequency",
                "updated_at",
            ]
        )

        LeaveAccrualService.accrue_month(
            organization=self.organization,
            year=2026,
            month=1,
        )

        self.client.force_authenticate(
            user=self.admin_user,
        )

        url = (
            f"/api/leave/"
            f"organizations/{self.organization.id}/"
            f"leave/balances/{self.balance.id}/"
        )

        response = self.client.get(
            url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["accrued_days"],
            Decimal("2.00"),
        )

        self.assertEqual(
            response.data["remaining_days"],
            Decimal("2.00"),
        )