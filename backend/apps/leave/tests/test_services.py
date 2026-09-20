from django.test import TestCase

from apps.leave.models import (
    LeaveBalance,
    LeavePolicy,
    LeaveRequest,
    LeaveType,
    WorkSchedule,
    PublicHoliday,
    LeaveBalanceAdjustment,
    LeaveApprovalStep,
    
)

from apps.employee.models import (
    Employment,
    Employee,
    EmployeeAssignment,
)
from apps.leave.services import (
    LeaveTypeService,
    LeavePolicyService,
    LeaveBalanceService,
    LeaveRequestService,
    LeaveCalendarService,
    EmployeeWorkScheduleService,
    LeaveEntitlementService,
    LeaveBalanceAdjustmentService,
    LeaveAccrualService,
    LeaveApprovalRuleService,
    LeaveApprovalService,

)
from apps.employee.services import (
    EmployeeService,
)
from apps.access.services import (
    AccessService,
    RoleService,
)
from apps.organization.models import Organization
from decimal import Decimal
from datetime import date
from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()

class LeaveTypeServiceTests(TestCase):

    def setUp(self):

        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
        )


    def test_create_leave_type(self):

        leave_type = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        self.assertEqual(
            leave_type.organization,
            self.organization,
        )

        self.assertEqual(
            leave_type.code,
            "ANNUAL",
        )

        self.assertTrue(
            leave_type.is_paid,
        )

    def test_duplicate_leave_type_code_is_rejected(
        self,
    ):

        LeaveTypeService.create_leave_type(
            organization=self.organization,
            code="ANNUAL",
            name="Annual Leave",
        )

        with self.assertRaises(ValueError):

            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Vacation",
            )

    def test_update_leave_type(self):

        leave_type = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        updated = (
            LeaveTypeService.update_leave_type(
                leave_type=leave_type,
                organization=self.organization,
                code="VACATION",
                name="Vacation Leave",
                description="Annual vacation entitlement.",
                is_paid=True,
                requires_approval=True,
            )
        )

        leave_type.refresh_from_db()

        self.assertEqual(
            updated.id,
            leave_type.id,
        )

        self.assertEqual(
            leave_type.code,
            "VACATION",
        )

        self.assertEqual(
            leave_type.name,
            "Vacation Leave",
        )

        self.assertEqual(
            leave_type.description,
            "Annual vacation entitlement.",
        )


    def test_update_leave_type_rejects_duplicate_code(
        self,
    ):

        annual = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        sick = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="SICK",
                name="Sick Leave",
            )
        )

        with self.assertRaises(ValueError):

            LeaveTypeService.update_leave_type(
                leave_type=sick,
                organization=self.organization,
                code="ANNUAL",
                name="Sick Leave",
            )

        annual.refresh_from_db()
        sick.refresh_from_db()

        self.assertEqual(
            annual.code,
            "ANNUAL",
        )

        self.assertEqual(
            sick.code,
            "SICK",
        )

    def test_update_leave_type_from_another_organization_is_rejected(
        self,
    ):

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        leave_type = (
            LeaveTypeService.create_leave_type(
                organization=another_organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        with self.assertRaises(ValueError):

            LeaveTypeService.update_leave_type(
                leave_type=leave_type,
                organization=self.organization,
                code="VACATION",
                name="Vacation Leave",
            )


    def test_deactivate_leave_type(self):

        leave_type = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        LeaveTypeService.deactivate_leave_type(
            leave_type=leave_type,
            organization=self.organization,
        )

        leave_type.refresh_from_db()

        self.assertFalse(
            leave_type.is_active,
        )

    def test_deactivate_already_inactive_leave_type_is_rejected(
        self,
    ):

        leave_type = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        LeaveTypeService.deactivate_leave_type(
            leave_type=leave_type,
            organization=self.organization,
        )

        with self.assertRaises(ValueError):

            LeaveTypeService.deactivate_leave_type(
                leave_type=leave_type,
                organization=self.organization,
            )

    def test_activate_leave_type(self):

        leave_type = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        LeaveTypeService.deactivate_leave_type(
            leave_type=leave_type,
            organization=self.organization,
        )

        LeaveTypeService.activate_leave_type(
            leave_type=leave_type,
            organization=self.organization,
        )

        leave_type.refresh_from_db()

        self.assertTrue(
            leave_type.is_active,
        )

    def test_activate_already_active_leave_type_is_rejected(
        self,
    ):

        leave_type = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        with self.assertRaises(ValueError):

            LeaveTypeService.activate_leave_type(
                leave_type=leave_type,
                organization=self.organization,
            )

class LeavePolicyServiceTests(TestCase):

    def setUp(self):

        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
        )

        self.leave_type = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

    def test_create_leave_policy(self):

        policy = (
            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=self.leave_type,
                days_per_year=20,
            )
        )

        self.assertEqual(
            policy.days_per_year,
            20,
        )

        self.assertFalse(
            policy.allow_carry_forward,
        )

    def test_leave_type_from_another_organization_is_rejected(
        self,
    ):

        another_organization = (
            Organization.objects.create(
                name="Another Company",
                legal_name="Another Company Limited",
            )
        )

        another_leave_type = (
            LeaveTypeService.create_leave_type(
                organization=another_organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        with self.assertRaises(ValueError):

            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=another_leave_type,
                days_per_year=20,
            )

    def test_minimum_request_cannot_exceed_maximum(
        self,
    ):

        with self.assertRaises(ValueError):

            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=self.leave_type,
                days_per_year=20,
                minimum_days_per_request=10,
                maximum_days_per_request=5,
            )


    def test_update_leave_policy(self):

        policy = (
            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=self.leave_type,
                days_per_year=20,
            )
        )

        updated = (
            LeavePolicyService.update_policy(
                policy=policy,
                organization=self.organization,
                days_per_year=25,
                minimum_days_per_request=1,
                maximum_days_per_request=10,
                allow_half_day=True,
                allow_carry_forward=True,
                maximum_carry_forward_days=5,
                requires_attachment=True,
            )
        )

        policy.refresh_from_db()

        self.assertEqual(
            updated.id,
            policy.id,
        )

        self.assertEqual(
            policy.days_per_year,
            25,
        )

        self.assertEqual(
            policy.minimum_days_per_request,
            1,
        )

        self.assertEqual(
            policy.maximum_days_per_request,
            10,
        )

        self.assertTrue(
            policy.allow_half_day,
        )

        self.assertTrue(
            policy.allow_carry_forward,
        )

        self.assertEqual(
            policy.maximum_carry_forward_days,
            5,
        )

        self.assertTrue(
            policy.requires_attachment,
        )

    def test_update_leave_policy_from_another_organization_is_rejected(
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

        policy = (
            LeavePolicyService.create_policy(
                organization=another_organization,
                leave_type=another_leave_type,
                days_per_year=20,
            )
        )

        with self.assertRaises(ValueError):

            LeavePolicyService.update_policy(
                policy=policy,
                organization=self.organization,
                days_per_year=25,
            )

    def test_update_leave_policy_rejects_invalid_request_range(
        self,
    ):

        policy = (
            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=self.leave_type,
                days_per_year=20,
            )
        )

        with self.assertRaises(ValueError):

            LeavePolicyService.update_policy(
                policy=policy,
                organization=self.organization,
                days_per_year=20,
                minimum_days_per_request=10,
                maximum_days_per_request=5,
            )

    def test_update_leave_policy_rejects_carry_forward_limit_when_disabled(
        self,
    ):

        policy = (
            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=self.leave_type,
                days_per_year=20,
            )
        )

        with self.assertRaises(ValueError):

            LeavePolicyService.update_policy(
                policy=policy,
                organization=self.organization,
                days_per_year=20,
                allow_carry_forward=False,
                maximum_carry_forward_days=5,
            )

    def test_update_leave_policy_rejects_carry_forward_limit_when_disabled(
        self,
    ):

        policy = (
            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=self.leave_type,
                days_per_year=20,
            )
        )

        with self.assertRaises(ValueError):

            LeavePolicyService.update_policy(
                policy=policy,
                organization=self.organization,
                days_per_year=20,
                allow_carry_forward=False,
                maximum_carry_forward_days=5,
            )

    def test_activate_leave_policy(self):

        policy = (
            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=self.leave_type,
                days_per_year=20,
            )
        )

        LeavePolicyService.deactivate_policy(
            policy=policy,
            organization=self.organization,
        )

        LeavePolicyService.activate_policy(
            policy=policy,
            organization=self.organization,
        )

        policy.refresh_from_db()

        self.assertTrue(
            policy.is_active,
        )

class LeaveBalanceServiceTests(TestCase):

    def setUp(self):

        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
        )

        # -----------------------------------
        # Reviewer / Admin User
        # -----------------------------------

        self.user = User.objects.create_user(
            email="admin@testcompany.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="Admin",
        )

        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="ORGANIZATION_ADMIN",
        )

        AccessService.assign_role(
            user=self.user,
            organization=self.organization,
            role=role,
        )

        self.employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john@testcompany.com",
        )

        self.leave_type = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        self.policy = (
            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=self.leave_type,
                days_per_year=20,
                allow_carry_forward=True,
                maximum_carry_forward_days=5,
            )
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



    def test_create_leave_balance(self):

        balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )
        )

        self.assertEqual(
            balance.entitlement_days,
            Decimal("20"),
        )

        self.assertEqual(
            balance.carry_forward_days,
            Decimal("0"),
        )

        self.assertEqual(
            balance.used_days,
            Decimal("0"),
        )

        self.assertEqual(
            balance.remaining_days,
            Decimal("20"),
        )

    def test_leave_balance_with_carry_forward(self):

        balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
                carry_forward_days=Decimal("5"),
            )
        )

        self.assertEqual(
            balance.total_available_days,
            Decimal("25"),
        )

        self.assertEqual(
            balance.remaining_days,
            Decimal("25"),
        )

    def test_remaining_days_after_usage(self):

        balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
                carry_forward_days=Decimal("5"),
            )
        )

        balance.used_days = Decimal("7")
        balance.save(
            update_fields=[
                "used_days",
                "updated_at",
            ]
        )

        self.assertEqual(
            balance.remaining_days,
            Decimal("18"),
        )

    def test_remaining_days_after_usage(self):

        balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
                carry_forward_days=Decimal("5"),
            )
        )

        balance.used_days = Decimal("7")
        balance.save(
            update_fields=[
                "used_days",
                "updated_at",
            ]
        )

        self.assertEqual(
            balance.remaining_days,
            Decimal("18"),
        )

    def test_leave_type_from_another_organization_is_rejected(
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

        with self.assertRaises(ValueError):

            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=another_leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )

    def test_carry_forward_is_rejected_when_policy_disallows_it(
        self,
    ):

        policy = (
            LeavePolicy.objects.get(
                id=self.policy.id,
            )
        )

        policy.allow_carry_forward = False
        policy.save(
            update_fields=[
                "allow_carry_forward",
            ]
        )

        with self.assertRaises(ValueError):

            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
                carry_forward_days=Decimal("2"),
            )

    def test_carry_forward_cannot_exceed_policy_limit(
        self,
    ):

        with self.assertRaises(ValueError):

            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
                carry_forward_days=Decimal("6"),
            )

    def test_entitlement_cannot_exceed_policy_allowance(
        self,
    ):

        with self.assertRaises(ValueError):

            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("21"),
            )

    def test_entitlement_cannot_exceed_policy_allowance(
        self,
    ):

        with self.assertRaises(ValueError):

            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("21"),
            )

    def test_duplicate_balance_is_rejected(self):

        LeaveBalanceService.create_balance(
            employee=self.employee,
            leave_type=self.leave_type,
            year=2026,
            entitlement_days=Decimal("20"),
        )

        with self.assertRaises(ValueError):

            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )


    def test_create_leave_request(self):

        balance = LeaveBalanceService.create_balance(
            employee=self.employee,
            leave_type=self.leave_type,
            year=2026,
            entitlement_days=Decimal("20"),
        )

        request = (
            LeaveRequestService.create_request(
                employee=self.employee,
                leave_type=self.leave_type,
                organization=self.organization,
                start_date=date(2026, 8, 24),
                end_date=date(2026, 8, 28),
                reason="Annual vacation",
            )
        )

        self.assertEqual(
            request.requested_days,
            Decimal("5"),
        )

        self.assertEqual(
            request.status,
            LeaveRequest.Status.DRAFT,
        )

        self.assertEqual(
            balance.remaining_days,
            Decimal("20"),
        )

    def test_approval_consumes_leave_balance(self):

        balance = LeaveBalanceService.create_balance(
            employee=self.employee,
            leave_type=self.leave_type,
            year=2026,
            entitlement_days=Decimal("20"),
        )

        request = LeaveRequestService.create_request(
            employee=self.employee,
            leave_type=self.leave_type,
            organization=self.organization,
            start_date=date(2026, 8, 24),
            end_date=date(2026, 8, 28),
        )

        LeaveRequestService.submit_request(
            leave_request=request,
            organization=self.organization,
        )

        LeaveRequestService.approve_request(
            leave_request=request,
            reviewed_by=self.user,
            organization=self.organization,
        )

        balance.refresh_from_db()

        self.assertEqual(
            balance.used_days,
            Decimal("5"),
        )

        self.assertEqual(
            balance.remaining_days,
            Decimal("15"),
        )


    def test_rejection_does_not_consume_balance(self):
    
        balance = LeaveBalanceService.create_balance(
            employee=self.employee,
            leave_type=self.leave_type,
            year=2026,
            entitlement_days=Decimal("20"),
        )

        request = LeaveRequestService.create_request(
            employee=self.employee,
            leave_type=self.leave_type,
            organization=self.organization,
            start_date=date(2026, 8, 24),
            end_date=date(2026, 8, 28),
        )

        LeaveRequestService.submit_request(
            leave_request=request,
            organization=self.organization,
        )

        LeaveRequestService.reject_request(
            leave_request=request,
            reviewed_by=self.user,
            organization=self.organization,
            review_comment="Too much leave requested.",
        )

        balance.refresh_from_db()

        self.assertEqual(
            balance.used_days,
            Decimal("0"),
        )

    def test_cancelling_approved_leave_restores_balance(
        self,
    ):

        balance = LeaveBalanceService.create_balance(
            employee=self.employee,
            leave_type=self.leave_type,
            year=2026,
            entitlement_days=Decimal("20"),
        )

        request = LeaveRequestService.create_request(
            employee=self.employee,
            leave_type=self.leave_type,
            organization=self.organization,
            start_date=date(2026, 8, 24),
            end_date=date(2026, 8, 28),
        )

        LeaveRequestService.submit_request(
            leave_request=request,
            organization=self.organization,
        )

        LeaveRequestService.approve_request(
            leave_request=request,
            reviewed_by=self.user,
            organization=self.organization
        )

        LeaveRequestService.cancel_request(
            leave_request=request,
        )

        balance.refresh_from_db()

        self.assertEqual(
            balance.used_days,
            Decimal("0"),
        )

        self.assertEqual(
            balance.remaining_days,
            Decimal("20"),
        )

    def test_initialize_year_creates_balance(self):

        balances = (
            LeaveBalanceService.initialize_year(
                organization=self.organization,
                year=2026,
            )
        )

        self.assertEqual(
            len(balances),
            1,
        )

        balance = balances[0]

        self.assertEqual(
            balance.year,
            2026,
        )

        self.assertEqual(
            balance.entitlement_days,
            Decimal("20"),
        )

        self.assertEqual(
            balance.carry_forward_days,
            Decimal("0"),
        )

        self.assertEqual(
            balance.used_days,
            Decimal("0"),
        )

    def test_initialize_year_is_idempotent(self):

        first_run = (
            LeaveBalanceService.initialize_year(
                organization=self.organization,
                year=2026,
            )
        )

        second_run = (
            LeaveBalanceService.initialize_year(
                organization=self.organization,
                year=2026,
            )
        )

        self.assertEqual(
            len(first_run),
            1,
        )

        self.assertEqual(
            len(second_run),
            0,
        )

        self.assertEqual(
            LeaveBalance.objects.filter(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
            ).count(),
            1,
        )

    def test_initialize_year_carries_forward_remaining_balance(
        self,
    ):

        previous_balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
                carry_forward_days=Decimal("0"),
            )
        )

        previous_balance.used_days = Decimal("15")

        previous_balance.save(
            update_fields=[
                "used_days",
                "updated_at",
            ]
        )

        balances = (
            LeaveBalanceService.initialize_year(
                organization=self.organization,
                year=2027,
            )
        )

        self.assertEqual(
            len(balances),
            1,
        )

        new_balance = balances[0]

        self.assertEqual(
            new_balance.entitlement_days,
            Decimal("20"),
        )

        self.assertEqual(
            new_balance.carry_forward_days,
            Decimal("5"),
        )

        self.assertEqual(
            new_balance.used_days,
            Decimal("0"),
        )

    def test_carry_forward_is_capped_by_policy(
        self,
    ):

        previous_balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )
        )

        previous_balance.used_days = Decimal("12")

        previous_balance.save(
            update_fields=[
                "used_days",
                "updated_at",
            ]
        )

        balances = (
            LeaveBalanceService.initialize_year(
                organization=self.organization,
                year=2027,
            )
        )

        new_balance = balances[0]

        self.assertEqual(
            new_balance.carry_forward_days,
            Decimal("5"),
        )

    def test_no_carry_forward_when_policy_disallows_it(
        self,
    ):

        self.policy.allow_carry_forward = False

        self.policy.save(
            update_fields=[
                "allow_carry_forward",
            ]
        )

        previous_balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )
        )

        previous_balance.used_days = Decimal("10")

        previous_balance.save(
            update_fields=[
                "used_days",
                "updated_at",
            ]
        )

        balances = (
            LeaveBalanceService.initialize_year(
                organization=self.organization,
                year=2027,
            )
        )

        self.assertEqual(
            balances[0].carry_forward_days,
            Decimal("0"),
        )

    def test_initialize_year_ignores_inactive_employees(
        self,
    ):

        self.employee.is_active = False

        self.employee.save(
            update_fields=[
                "is_active",
            ]
        )

        balances = (
            LeaveBalanceService.initialize_year(
                organization=self.organization,
                year=2026,
            )
        )

        self.assertEqual(
            len(balances),
            0,
        )

    def test_initialize_year_ignores_inactive_policies(
        self,
    ):

        self.policy.is_active = False

        self.policy.save(
            update_fields=[
                "is_active",
            ]
        )

        balances = (
            LeaveBalanceService.initialize_year(
                organization=self.organization,
                year=2026,
            )
        )

        self.assertEqual(
            len(balances),
            0,
        )

    def test_create_employee_leave_entitlement(
        self,
    ):

        entitlement = (
            LeaveEntitlementService
            .create_entitlement(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                days=Decimal("25"),
                is_override=True,
                reason="Senior grade entitlement.",
            )
        )

        self.assertEqual(
            entitlement.days,
            Decimal("25"),
        )

        self.assertTrue(
            entitlement.is_override,
        )

    def test_duplicate_employee_entitlement_is_rejected(
        self,
    ):

        LeaveEntitlementService.create_entitlement(
            employee=self.employee,
            leave_type=self.leave_type,
            year=2026,
            days=Decimal("25"),
        )

        with self.assertRaises(ValueError):

            LeaveEntitlementService.create_entitlement(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                days=Decimal("20"),
            )

    def test_effective_entitlement_uses_override(
        self,
    ):

        LeaveEntitlementService.create_entitlement(
            employee=self.employee,
            leave_type=self.leave_type,
            year=2026,
            days=Decimal("25"),
            is_override=True,
        )

        days = (
            LeaveEntitlementService
            .get_effective_days(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
            )
        )

        self.assertEqual(
            days,
            Decimal("25"),
        )

    def test_effective_entitlement_falls_back_to_policy(
        self,
    ):

        days = (
            LeaveEntitlementService
            .get_effective_days(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
            )
        )

        self.assertEqual(
            days,
            Decimal("20"),
        )

    def test_initialize_year_uses_employee_entitlement(
        self,
    ):

        LeaveEntitlementService.create_entitlement(
            employee=self.employee,
            leave_type=self.leave_type,
            year=2026,
            days=Decimal("25"),
            is_override=True,
        )

        balances = (
            LeaveBalanceService.initialize_year(
                organization=self.organization,
                year=2026,
            )
        )

        self.assertEqual(
            balances[0].entitlement_days,
            Decimal("25"),
        )

    def test_prorated_entitlement_for_mid_year_employee(
        self,
    ):
        days = (
            LeaveEntitlementService
            .calculate_prorated_days(
                annual_days=Decimal("20"),
                start_date=date(2026, 7, 1),
                year=2026,
            )
        )
    
        self.assertEqual(
            days,
            Decimal("10.00"),
        )
    
    def test_january_employee_gets_full_entitlement(
        self,
    ):
        days = (
            LeaveEntitlementService
            .calculate_prorated_days(
                annual_days=Decimal("20"),
                start_date=date(2026, 1, 1),
                year=2026,
            )
        )
    
        self.assertEqual(
            days,
            Decimal("20.00"),
        )
    
    def test_december_employee_gets_one_month_proration(
        self,
    ):
        days = (
            LeaveEntitlementService
            .calculate_prorated_days(
                annual_days=Decimal("20"),
                start_date=date(2026, 12, 1),
                year=2026,
            )
        )
    
        self.assertEqual(
            days,
            Decimal("1.67"),
        )
    
    def test_employee_who_started_before_year_gets_full_entitlement(
        self,
    ):
        days = (
            LeaveEntitlementService
            .calculate_prorated_days(
                annual_days=Decimal("20"),
                start_date=date(2024, 5, 1),
                year=2026,
            )
        )
    
        self.assertEqual(
            days,
            Decimal("20.00"),
        )
    
    def test_future_employee_gets_zero_entitlement(
        self,
    ):
        days = (
            LeaveEntitlementService
            .calculate_prorated_days(
                annual_days=Decimal("20"),
                start_date=date(2027, 1, 1),
                year=2026,
            )
        )
    
        self.assertEqual(
            days,
            Decimal("0.00"),
        )
    
    def test_policy_without_proration_uses_full_entitlement(
        self,
    ):
        self.policy.prorate_for_new_hires = False
    
        self.policy.save(
            update_fields=[
                "prorate_for_new_hires",
            ]
        )
    
        days = (
            LeaveEntitlementService
            .get_effective_days(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
            )
        )
    
        self.assertEqual(
            days,
            Decimal("20"),
        )
    
    def test_initialize_year_uses_prorated_entitlement(
        self,
    ):
        self.policy.prorate_for_new_hires = True

        self.policy.save(
            update_fields=[
                "prorate_for_new_hires",
            ]
        )

        employment = Employment.objects.get(
            employee=self.employee,
        )

        employment.employment_start_date = date(
            2026,
            7,
            1,
        )

        employment.save(
            update_fields=[
                "employment_start_date",
                "updated_at",
            ]
        )

        balances = (
            LeaveBalanceService
            .initialize_year(
                organization=self.organization,
                year=2026,
            )
        )

        self.assertEqual(
            balances[0].entitlement_days,
            Decimal("10.00"),
        )

    def test_credit_adjustment_increases_available_balance(
        self,
    ):

        balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
                carry_forward_days=Decimal("0"),
            )
        )

        self.assertEqual(
            balance.remaining_days,
            Decimal("20"),
        )

        adjustment = (
            LeaveBalanceAdjustmentService
            .create_adjustment(
                balance=balance,
                organization=self.organization,
                adjusted_by=self.user,
                amount=Decimal("3"),
                adjustment_type=(
                    LeaveBalanceAdjustment
                    .AdjustmentType.CREDIT
                ),
                reason="Management granted additional leave.",
            )
        )

        self.assertEqual(
            adjustment.amount,
            Decimal("3"),
        )

        balance.refresh_from_db()

        self.assertEqual(
            balance.remaining_days,
            Decimal("23"),
        )

    def test_debit_adjustment_reduces_available_balance(
        self,
    ):

        balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
                carry_forward_days=Decimal("0"),
            )
        )

        adjustment = (
            LeaveBalanceAdjustmentService
            .create_adjustment(
                balance=balance,
                organization=self.organization,
                adjusted_by=self.user,
                amount=Decimal("3"),
                adjustment_type=(
                    LeaveBalanceAdjustment
                    .AdjustmentType.DEBIT
                ),
                reason="Leave correction.",
            )
        )

        self.assertEqual(
            adjustment.amount,
            Decimal("3"),
        )

        balance.refresh_from_db()

        self.assertEqual(
            balance.remaining_days,
            Decimal("17"),
        )

    def test_debit_adjustment_cannot_make_balance_negative(
        self,
    ):

        balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
                carry_forward_days=Decimal("0"),
            )
        )

        with self.assertRaises(ValueError):

            LeaveBalanceAdjustmentService.create_adjustment(
                balance=balance,
                organization=self.organization,
                adjusted_by=self.user,
                amount=Decimal("25"),
                adjustment_type=(
                    LeaveBalanceAdjustment
                    .AdjustmentType.DEBIT
                ),
                reason="Invalid correction.",
            )

    def test_adjustment_requires_reason(
        self,
    ):

        balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
                carry_forward_days=Decimal("0"),
            )
        )

        with self.assertRaises(ValueError):

            LeaveBalanceAdjustmentService.create_adjustment(
                balance=balance,
                organization=self.organization,
                adjusted_by=self.user,
                amount=Decimal("2"),
                adjustment_type=(
                    LeaveBalanceAdjustment
                    .AdjustmentType.CREDIT
                ),
                reason="",
            )

    def test_adjustment_cannot_target_another_organization(
        self,
    ):

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
                carry_forward_days=Decimal("0"),
            )
        )

        with self.assertRaises(ValueError):

            LeaveBalanceAdjustmentService.create_adjustment(
                balance=balance,
                organization=another_organization,
                adjusted_by=self.user,
                amount=Decimal("2"),
                adjustment_type=(
                    LeaveBalanceAdjustment
                    .AdjustmentType.CREDIT
                ),
                reason="Invalid organization.",
            )


    def test_monthly_accrual_calculation(self):

        self.balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )
        )

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

        accruals = (
            LeaveAccrualService.accrue_month(
                organization=self.organization,
                year=2026,
                month=1,
            )
        )

        self.assertEqual(
            accruals[0].amount,
            Decimal("2.00"),
        )


    def test_monthly_accrual_is_idempotent(self):

        self.balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )
        )

        self.balance.accrual_enabled = True
        self.balance.accrual_frequency = "MONTHLY"

        self.balance.save(
            update_fields=[
                "accrual_enabled",
                "accrual_frequency",
                "updated_at",
            ]
        )

        first = (
            LeaveAccrualService.accrue_month(
                organization=self.organization,
                year=2026,
                month=1,
            )
        )

        second = (
            LeaveAccrualService.accrue_month(
                organization=self.organization,
                year=2026,
                month=1,
            )
        )

        self.assertEqual(
            len(first),
            1,
        )

        self.assertEqual(
            len(second),
            0,
        )


    def test_twelve_months_equal_annual_entitlement(
        self,
    ):

        self.balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )
        )

        self.balance.accrual_enabled = True
        self.balance.accrual_frequency = "MONTHLY"

        self.balance.save(
            update_fields=[
                "accrual_enabled",
                "accrual_frequency",
                "updated_at",
            ]
        )

        for month in range(1, 13):

            LeaveAccrualService.accrue_month(
                organization=self.organization,
                year=2026,
                month=month,
            )

        self.assertEqual(
            self.balance.accrued_days,
            Decimal("20.00"),
        )


    def test_accrual_increases_remaining_balance(
        self,
    ):

        self.balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )
        )

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

        self.balance.refresh_from_db()

        self.assertEqual(
            self.balance.remaining_days,
            Decimal("2.00"),
        )

    def test_annual_policy_is_not_monthly_accrued(
        self,
    ):

        self.balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )
        )

        self.balance.accrual_enabled = False

        self.balance.save(
            update_fields=[
                "accrual_enabled",
                "updated_at",
            ]
        )

        accruals = (
            LeaveAccrualService.accrue_month(
                organization=self.organization,
                year=2026,
                month=1,
            )
        )

        self.assertEqual(
            len(accruals),
            0,
        )



class LeaveCalendarServiceTests(TestCase):

    def setUp(self):

        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
        )

        # -----------------------------------
        # Work Schedule
        # -----------------------------------

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

        # -----------------------------------
        # Employee
        # -----------------------------------

        self.employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john@testcompany.com",
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

        self.policy = (
            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=self.leave_type,
                days_per_year=20,
            )
        )
        
    def test_calculate_working_days(self):

        total = (
            LeaveCalendarService
            .calculate_working_days(
                organization=self.organization,
                work_schedule=self.work_schedule,
                start_date=date(2026, 8, 24),
                end_date=date(2026, 8, 28),
            )
        )

        self.assertEqual(
            total,
            Decimal("5"),
        )

    def test_weekend_days_are_excluded(self):

        total = (
            LeaveCalendarService
            .calculate_working_days(
                organization=self.organization,
                work_schedule=self.work_schedule,
                start_date=date(2026, 8, 28),
                end_date=date(2026, 8, 31),
            )
        )

        self.assertEqual(
            total,
            Decimal("2"),
        )

    def test_public_holiday_is_excluded(self):

        PublicHoliday.objects.create(
            organization=self.organization,
            date=date(2026, 8, 26),
            name="Test Holiday",
        )

        total = (
            LeaveCalendarService
            .calculate_working_days(
                organization=self.organization,
                work_schedule=self.work_schedule,
                start_date=date(2026, 8, 24),
                end_date=date(2026, 8, 28),
            )
        )

        self.assertEqual(
            total,
            Decimal("4"),
        )

    def test_saturday_can_be_a_working_day(self):

        schedule = WorkSchedule.objects.create(
            organization=self.organization,
            code="MON_SAT",
            name="Monday to Saturday",
            monday=True,
            tuesday=True,
            wednesday=True,
            thursday=True,
            friday=True,
            saturday=True,
            sunday=False,
        )

        total = (
            LeaveCalendarService
            .calculate_working_days(
                organization=self.organization,
                work_schedule=schedule,
                start_date=date(2026, 8, 24),
                end_date=date(2026, 8, 29),
            )
        )

        self.assertEqual(
            total,
            Decimal("6"),
        )

    def test_schedule_from_another_organization_is_rejected(
        self,
    ):

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_schedule = WorkSchedule.objects.create(
            organization=another_organization,
            code="MON_FRI",
            name="Monday to Friday",
        )

        with self.assertRaises(ValueError):

            LeaveCalendarService.calculate_working_days(
                organization=self.organization,
                work_schedule=another_schedule,
                start_date=date(2026, 8, 24),
                end_date=date(2026, 8, 28),
        )

    def test_leave_request_uses_working_days(
        self,
    ):

        request = LeaveRequestService.create_request(
            employee=self.employee,
            leave_type=self.leave_type,
            organization=self.organization,
            start_date=date(2026, 8, 28),
            end_date=date(2026, 8, 31),
            reason="Weekend-spanning leave",
        )

        self.assertEqual(
            request.requested_days,
            Decimal("2"),
        )

    def test_leave_request_excludes_public_holiday(
        self,
    ):

        PublicHoliday.objects.create(
            organization=self.organization,
            date=date(2026, 8, 26),
            name="Test Holiday",
        )

        request = LeaveRequestService.create_request(
            employee=self.employee,
            leave_type=self.leave_type,
            organization=self.organization,
            start_date=date(2026, 8, 24),
            end_date=date(2026, 8, 28),
        )

        self.assertEqual(
            request.requested_days,
            Decimal("4"),
        )

class EmployeeWorkScheduleServiceTests(
    TestCase
):

    def setUp(self):

        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
        )

        self.employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john@testcompany.com",
        )

        self.default_schedule = (
            WorkSchedule.objects.create(
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
        )

        self.saturday_schedule = (
            WorkSchedule.objects.create(
                organization=self.organization,
                code="MON_SAT",
                name="Monday to Saturday",
                monday=True,
                tuesday=True,
                wednesday=True,
                thursday=True,
                friday=True,
                saturday=True,
                sunday=False,
                is_default=False,
                is_active=True,
            )
        )

    def test_assign_employee_work_schedule(self):

        assignment = (
            EmployeeWorkScheduleService
            .assign_schedule(
                employee=self.employee,
                work_schedule=self.saturday_schedule,
                effective_from=date(2026, 7, 1),
            )
        )

        self.assertEqual(
            assignment.employee,
            self.employee,
        )

        self.assertEqual(
            assignment.work_schedule,
            self.saturday_schedule,
        )

    def test_get_schedule_for_date_uses_employee_schedule(
        self,
    ):

        EmployeeWorkScheduleService.assign_schedule(
            employee=self.employee,
            work_schedule=self.saturday_schedule,
            effective_from=date(2026, 7, 1),
        )

        schedule = (
            EmployeeWorkScheduleService
            .get_schedule_for_date(
                employee=self.employee,
                day=date(2026, 7, 15),
            )
        )

        self.assertEqual(
            schedule,
            self.saturday_schedule,
        )

    def test_get_schedule_for_date_falls_back_to_default(
        self,
    ):

        schedule = (
            EmployeeWorkScheduleService
            .get_schedule_for_date(
                employee=self.employee,
                day=date(2026, 6, 15),
            )
        )

        self.assertEqual(
            schedule,
            self.default_schedule,
        )

    def test_schedule_changes_over_time(self):

        EmployeeWorkScheduleService.assign_schedule(
            employee=self.employee,
            work_schedule=self.default_schedule,
            effective_from=date(2026, 1, 1),
            effective_to=date(2026, 6, 30),
        )

        EmployeeWorkScheduleService.assign_schedule(
            employee=self.employee,
            work_schedule=self.saturday_schedule,
            effective_from=date(2026, 7, 1),
        )

        june_schedule = (
            EmployeeWorkScheduleService
            .get_schedule_for_date(
                employee=self.employee,
                day=date(2026, 6, 30),
            )
        )

        july_schedule = (
            EmployeeWorkScheduleService
            .get_schedule_for_date(
                employee=self.employee,
                day=date(2026, 7, 1),
            )
        )

        self.assertEqual(
            june_schedule,
            self.default_schedule,
        )

        self.assertEqual(
            july_schedule,
            self.saturday_schedule,
        )

    def test_overlapping_schedule_assignment_is_rejected(
        self,
    ):

        EmployeeWorkScheduleService.assign_schedule(
            employee=self.employee,
            work_schedule=self.default_schedule,
            effective_from=date(2026, 1, 1),
            effective_to=date(2026, 6, 30),
        )

        with self.assertRaises(ValueError):

            EmployeeWorkScheduleService.assign_schedule(
                employee=self.employee,
                work_schedule=self.saturday_schedule,
                effective_from=date(2026, 6, 1),
                effective_to=date(2026, 12, 31),
            )

    def test_schedule_from_another_organization_is_rejected(
        self,
    ):

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_schedule = (
            WorkSchedule.objects.create(
                organization=another_organization,
                code="MON_SAT",
                name="Monday to Saturday",
            )
        )

        with self.assertRaises(ValueError):

            EmployeeWorkScheduleService.assign_schedule(
                employee=self.employee,
                work_schedule=another_schedule,
                effective_from=date(2026, 7, 1),
            )

    def test_employee_calendar_uses_employee_schedule(
        self,
    ):

        EmployeeWorkScheduleService.assign_schedule(
            employee=self.employee,
            work_schedule=self.saturday_schedule,
            effective_from=date(2026, 7, 1),
        )

        total = (
            LeaveCalendarService
            .calculate_employee_working_days(
                employee=self.employee,
                start_date=date(2026, 7, 4),
                end_date=date(2026, 7, 5),
            )
        )

        self.assertEqual(
            total,
            Decimal("1"),
        )


class LeaveApprovalServiceTests(TestCase):

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
        )

        self.employee_user = (
            User.objects.create_user(
                email="employee@testcompany.com",
                password="TestPassword123!",
                first_name="John",
                last_name="Employee",
            )
        )

        self.manager_user = (
            User.objects.create_user(
                email="manager@testcompany.com",
                password="TestPassword123!",
                first_name="Jane",
                last_name="Manager",
            )
        )

        self.senior_manager_user = (
            User.objects.create_user(
                email="senior@testcompany.com",
                password="TestPassword123!",
                first_name="Mike",
                last_name="Senior",
            )
        )

        self.employee = Employee.objects.create(
            organization=self.organization,
            user=self.employee_user,
            employee_number="EMP001",
        )

        self.manager = Employee.objects.create(
            organization=self.organization,
            user=self.manager_user,
            employee_number="EMP002",
        )

        self.senior_manager = Employee.objects.create(
            organization=self.organization,
            user=self.senior_manager_user,
            employee_number="EMP003",
        )

        EmployeeAssignment.objects.create(
            employee=self.employee,
            manager=self.manager,
        )

        EmployeeAssignment.objects.create(
            employee=self.manager,
            manager=self.senior_manager,
        )

        role = (
            RoleService.provision_system_role(
                organization=self.organization,
                role_code="ORGANIZATION_ADMIN",
            )
        )

        AccessService.assign_role(
            user=self.manager_user,
            organization=self.organization,
            role=role,
        )

        AccessService.assign_role(
            user=self.senior_manager_user,
            organization=self.organization,
            role=role,
        )

        self.leave_type = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        self.policy = (
            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=self.leave_type,
                days_per_year=20,
            )
        )

        self.balance = (
            LeaveBalanceService.create_balance(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
                entitlement_days=Decimal("20"),
            )
        )
        
    def create_request(self):

        return (
            LeaveRequestService.create_request(
                employee=self.employee,
                leave_type=self.leave_type,
                organization=self.organization,
                start_date=date(
                    2026,
                    8,
                    24,
                ),
                end_date=date(
                    2026,
                    8,
                    28,
                ),
            )
        )

    def test_manager_level_one_resolution(self):

        manager = (
            LeaveApprovalService
            .get_manager_at_level(
                employee=self.employee,
                approval_level=1,
            )
        )

        self.assertEqual(
            manager,
            self.manager,
        )

    def test_manager_level_two_resolution(self):

        manager = (
            LeaveApprovalService
            .get_manager_at_level(
                employee=self.employee,
                approval_level=2,
            )
        )

        self.assertEqual(
            manager,
            self.senior_manager,
        )

    def test_create_sequential_approval_chain(self):

        LeaveApprovalRuleService.create_rule(
            organization=self.organization,
            leave_type=self.leave_type,
            approval_level=1,
        )

        LeaveApprovalRuleService.create_rule(
            organization=self.organization,
            leave_type=self.leave_type,
            approval_level=2,
        )

        request = self.create_request()

        LeaveRequestService.submit_request(
            leave_request=request,
            organization=self.organization,
        )

        steps = list(
            request.approval_steps.all()
        )

        self.assertEqual(
            len(steps),
            2,
        )

        self.assertEqual(
            steps[0].approval_level,
            1,
        )

        self.assertEqual(
            steps[0].approver_user,
            self.manager_user,
        )

        self.assertEqual(
            steps[1].approval_level,
            2,
        )

        self.assertEqual(
            steps[1].approver_user,
            self.senior_manager_user,
        )

    def test_first_approval_does_not_consume_balance(
        self,
    ):

        LeaveApprovalRuleService.create_rule(
            organization=self.organization,
            leave_type=self.leave_type,
            approval_level=1,
        )

        LeaveApprovalRuleService.create_rule(
            organization=self.organization,
            leave_type=self.leave_type,
            approval_level=2,
        )

        request = self.create_request()

        LeaveRequestService.submit_request(
            leave_request=request,
            organization=self.organization,
        )

        LeaveRequestService.approve_request(
            leave_request=request,
            reviewed_by=self.manager_user,
            organization=self.organization,
        )

        request.refresh_from_db()
        self.balance.refresh_from_db()

        self.assertEqual(
            request.status,
            LeaveRequest.Status.SUBMITTED,
        )

        self.assertEqual(
            self.balance.used_days,
            Decimal("0"),
        )

        step = (
            LeaveApprovalStep.objects.get(
                leave_request=request,
                approval_level=1,
            )
        )

        self.assertEqual(
            step.status,
            LeaveApprovalStep.Status.APPROVED,
        )

    def test_final_approval_consumes_balance(
        self,
    ):

        LeaveApprovalRuleService.create_rule(
            organization=self.organization,
            leave_type=self.leave_type,
            approval_level=1,
        )

        LeaveApprovalRuleService.create_rule(
            organization=self.organization,
            leave_type=self.leave_type,
            approval_level=2,
        )

        request = self.create_request()

        LeaveRequestService.submit_request(
            leave_request=request,
            organization=self.organization,
        )

        LeaveRequestService.approve_request(
            leave_request=request,
            reviewed_by=self.manager_user,
            organization=self.organization,
        )

        LeaveRequestService.approve_request(
            leave_request=request,
            reviewed_by=self.senior_manager_user,
            organization=self.organization,
        )

        request.refresh_from_db()
        self.balance.refresh_from_db()

        self.assertEqual(
            request.status,
            LeaveRequest.Status.APPROVED,
        )

        self.assertEqual(
            self.balance.used_days,
            Decimal("5"),
        )

    def test_non_current_approver_cannot_approve(
        self,
    ):

        LeaveApprovalRuleService.create_rule(
            organization=self.organization,
            leave_type=self.leave_type,
            approval_level=1,
        )

        LeaveApprovalRuleService.create_rule(
            organization=self.organization,
            leave_type=self.leave_type,
            approval_level=2,
        )

        request = self.create_request()

        LeaveRequestService.submit_request(
            leave_request=request,
            organization=self.organization,
        )

        with self.assertRaises(PermissionError):

            LeaveApprovalService.approve_current_step(
                leave_request=request,
                user=self.senior_manager_user,
            )

    def test_rejection_skips_remaining_steps(
        self,
    ):

        LeaveApprovalRuleService.create_rule(
            organization=self.organization,
            leave_type=self.leave_type,
            approval_level=1,
        )

        LeaveApprovalRuleService.create_rule(
            organization=self.organization,
            leave_type=self.leave_type,
            approval_level=2,
        )

        request = self.create_request()

        LeaveRequestService.submit_request(
            leave_request=request,
            organization=self.organization,
        )

        LeaveRequestService.reject_request(
            leave_request=request,
            reviewed_by=self.manager_user,
            organization=self.organization,
            review_comment="Not approved.",
        )

        request.refresh_from_db()
        self.balance.refresh_from_db()

        steps = list(
            request.approval_steps
            .order_by("approval_level")
        )

        self.assertEqual(
            request.status,
            LeaveRequest.Status.REJECTED,
        )

        self.assertEqual(
            steps[0].status,
            LeaveApprovalStep.Status.REJECTED,
        )

        self.assertEqual(
            steps[1].status,
            LeaveApprovalStep.Status.SKIPPED,
        )

        self.assertEqual(
            self.balance.used_days,
            Decimal("0"),
        )

    def test_no_approval_rules_preserve_existing_manual_flow(
        self,
    ):

        request = self.create_request()

        LeaveRequestService.submit_request(
            leave_request=request,
            organization=self.organization,
        )

        self.assertEqual(
            request.approval_steps.count(),
            0,
        )

        LeaveRequestService.approve_request(
            leave_request=request,
            reviewed_by=self.manager_user,
            organization=self.organization,
        )

        request.refresh_from_db()

        self.assertEqual(
            request.status,
            LeaveRequest.Status.APPROVED,
        )

        self.balance.refresh_from_db()

        self.assertEqual(
            self.balance.used_days,
            Decimal("5"),
        )