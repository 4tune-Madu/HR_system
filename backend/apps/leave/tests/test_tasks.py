from decimal import Decimal
from django.test import TestCase

from apps.organization.models import Organization
from apps.employee.services import EmployeeService

from apps.leave.tasks import (
    initialize_leave_balances_for_organization,
)

from apps.leave.models import (
    LeaveBalance,
    LeaveType,
    LeavePolicy,
    LeaveAccrual,
)

from apps.leave.services import (
    LeaveBalanceService,
    LeaveTypeService,
    LeavePolicyService,
)

from apps.leave.tasks import (
    accrue_leave_for_organization,
)


class LeaveAccrualTaskTests(TestCase):

    def setUp(self):

        # -----------------------------------
        # Organization
        # -----------------------------------

        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
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
                days_per_year=Decimal("24"),
                accrual_enabled=True,
                accrual_frequency="MONTHLY",
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
                entitlement_days=Decimal("24"),
            )
        )

    def test_task_accrues_leave(
        self,
    ):

        result = (
            accrue_leave_for_organization.apply(
                args=[
                    str(
                        self.organization.id
                    ),
                    2026,
                    1,
                ]
            ).get()
        )

        self.assertEqual(
            result["created"],
            1,
        )

        self.assertEqual(
            LeaveAccrual.objects.filter(
                balance=self.balance,
                year=2026,
                period_month=1,
            ).count(),
            1,
        )

    def test_task_is_idempotent(
        self,
    ):

        first = (
            accrue_leave_for_organization.apply(
                args=[
                    str(
                        self.organization.id
                    ),
                    2026,
                    1,
                ]
            ).get()
        )

        second = (
            accrue_leave_for_organization.apply(
                args=[
                    str(
                        self.organization.id
                    ),
                    2026,
                    1,
                ]
            ).get()
        )

        self.assertEqual(
            first["created"],
            1,
        )

        self.assertEqual(
            second["created"],
            0,
        )

    def test_initialize_year_task(
        self,
    ):

        self.balance.delete()

        result = (
            initialize_leave_balances_for_organization.apply(
                args=[
                    str(
                        self.organization.id
                    ),
                    2026,
                ]
            ).get()
        )

        self.assertEqual(
            result["balances_created"],
            1,
        )

        self.assertTrue(
            LeaveBalance.objects.filter(
                employee=self.employee,
                leave_type=self.leave_type,
                year=2026,
            ).exists()
        )

    def test_initialize_year_task_is_idempotent(
        self,
    ):
    
        self.balance.delete()
    
        first = (
            initialize_leave_balances_for_organization.apply(
                args=[
                    str(
                        self.organization.id
                    ),
                    2026,
                ]
            ).get()
        )
    
        second = (
            initialize_leave_balances_for_organization.apply(
                args=[
                    str(
                        self.organization.id
                    ),
                    2026,
                ]
            ).get()
        )
    
        self.assertEqual(
            first["balances_created"],
            1,
        )
    
        self.assertEqual(
            second["balances_created"],
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
        

    def test_full_annual_leave_lifecycle(
        self,
    ):

        initialize_leave_balances_for_organization.apply(
            args=[
                str(
                    self.organization.id
                ),
                2026,
            ]
        ).get()

        self.balance.refresh_from_db()

        self.balance.accrual_enabled = True
        self.balance.accrual_frequency = "MONTHLY"
        self.balance.entitlement_days = Decimal("24")

        self.balance.save(
            update_fields=[
                "accrual_enabled",
                "accrual_frequency",
                "entitlement_days",
                "updated_at",
            ]
        )

        for month in range(1, 13):

            accrue_leave_for_organization.apply(
                args=[
                    str(
                        self.organization.id
                    ),
                    2026,
                    month,
                ]
            ).get()

        self.assertEqual(
            self.balance.accrued_days,
            Decimal("24.00"),
        )