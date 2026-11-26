from datetime import date
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.access.services import AccessService, RoleService
from apps.accounts.models import User
from apps.employee.services import EmployeeService
from apps.organization.models import Organization
from apps.authentication.serializers import MeSerializer

from apps.payroll.models import EmployeeCompensation, EmployeePayrollComponent, PayrollEntry, PayrollPeriod, PayrollRun


class PayrollAPITests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Payroll Test Company",
            legal_name="Payroll Test Company Limited",
        )
        self.user = User.objects.create_user(
            email="payroll@testcompany.com",
            password="TestPassword123!",
        )
        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="PAYROLL_ADMIN",
        )
        AccessService.assign_role(user=self.user, organization=self.organization, role=role)
        self.employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="Ada",
            last_name="Okafor",
            company_email="ada@testcompany.com",
        )
        self.client.force_authenticate(user=self.user)

    def periods_url(self):
        return f"/api/payroll/organizations/{self.organization.id}/payroll/periods/"

    def compensation_url(self):
        return f"/api/payroll/organizations/{self.organization.id}/payroll/compensation/"

    def components_url(self):
        return f"/api/payroll/organizations/{self.organization.id}/payroll/components/"

    def test_period_rejects_reversed_dates(self):
        response = self.client.post(self.periods_url(), {
            "name": "Invalid period",
            "start_date": "2026-10-31",
            "end_date": "2026-10-01",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_process_applies_earnings_and_deductions(self):
        self.client.post(self.compensation_url(), {
            "employee": str(self.employee.id),
            "monthly_gross": "100000.00",
            "effective_from": "2026-10-01",
        }, format="json")
        self.client.post(self.components_url(), {
            "employee": str(self.employee.id),
            "name": "Transport allowance",
            "kind": "EARNING",
            "amount": "15000.00",
            "effective_from": "2026-10-01",
        }, format="json")
        self.client.post(self.components_url(), {
            "employee": str(self.employee.id),
            "name": "Staff loan",
            "kind": "DEDUCTION",
            "amount": "5000.00",
            "effective_from": "2026-10-01",
        }, format="json")
        period = self.client.post(self.periods_url(), {
            "name": "October 2026",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        }, format="json").data

        response = self.client.post(f"{self.periods_url()}{period['id']}/process/")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data["total_gross"]), Decimal("115000.00"))
        self.assertEqual(Decimal(response.data["total_deductions"]), Decimal("5000.00"))
        self.assertEqual(Decimal(response.data["total_net"]), Decimal("110000.00"))
        entry = PayrollEntry.objects.get(run__period_id=period["id"])
        self.assertEqual(entry.net_pay, Decimal("110000.00"))

    def test_approved_run_cannot_be_approved_twice(self):
        from apps.payroll.models import EmployeeCompensation

        EmployeeCompensation.objects.create(
            employee=self.employee,
            monthly_gross=Decimal("100000.00"),
            effective_from=date(2026, 10, 1),
        )
        period = self.client.post(self.periods_url(), {
            "name": "October 2026",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        }, format="json").data
        run = self.client.post(f"{self.periods_url()}{period['id']}/process/").data
        approve_url = f"/api/payroll/organizations/{self.organization.id}/payroll/runs/{run['id']}/approve/"

        self.assertEqual(self.client.post(approve_url).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(approve_url).status_code, status.HTTP_400_BAD_REQUEST)

    def test_future_compensation_does_not_create_a_payroll_run(self):
        EmployeeCompensation.objects.create(
            employee=self.employee,
            monthly_gross=Decimal("100000.00"),
            effective_from=date(2026, 11, 1),
        )
        period = PayrollPeriod.objects.create(
            organization=self.organization,
            name="October 2026",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
        )

        response = self.client.post(f"{self.periods_url()}{period.id}/process/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PayrollRun.objects.filter(period=period).exists())
        period.refresh_from_db()
        self.assertEqual(period.status, PayrollPeriod.Status.OPEN)

    def test_process_excludes_future_compensation_and_components(self):
        EmployeeCompensation.objects.create(
            employee=self.employee,
            monthly_gross=Decimal("100000.00"),
            effective_from=date(2026, 10, 31),
        )
        future_employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="Future",
            last_name="Employee",
            company_email="future@testcompany.com",
        )
        EmployeeCompensation.objects.create(
            employee=future_employee,
            monthly_gross=Decimal("200000.00"),
            effective_from=date(2026, 11, 1),
        )
        for kind in EmployeePayrollComponent.Kind.values:
            EmployeePayrollComponent.objects.create(
                employee=self.employee, name=f"Future {kind}", kind=kind,
                amount=Decimal("5000.00"), effective_from=date(2026, 11, 1),
            )
        EmployeePayrollComponent.objects.create(
            employee=self.employee, name="Effective allowance", kind="EARNING",
            amount=Decimal("15000.00"), effective_from=date(2026, 10, 31),
        )
        period = PayrollPeriod.objects.create(
            organization=self.organization,
            name="October 2026",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
        )

        response = self.client.post(f"{self.periods_url()}{period.id}/process/")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data["total_gross"]), Decimal("115000.00"))
        self.assertEqual(Decimal(response.data["total_deductions"]), Decimal("0.00"))
        self.assertEqual(Decimal(response.data["total_net"]), Decimal("115000.00"))
        entries = PayrollEntry.objects.filter(run__period=period)
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.get().employee_id, self.employee.id)

    def test_compensation_list_is_organization_scoped(self):
        response = self.client.get(self.compensation_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

    def test_employee_can_view_only_approved_own_payroll(self):
        employee_role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="EMPLOYEE",
        )
        AccessService.assign_role(user=self.user, organization=self.organization, role=employee_role)
        self.employee.user = self.user
        self.employee.save(update_fields=["user"])
        period = PayrollPeriod.objects.create(
            organization=self.organization,
            name="September 2026",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            status=PayrollPeriod.Status.APPROVED,
        )
        run = PayrollRun.objects.create(
            period=period,
            total_gross=Decimal("100000.00"),
            total_net=Decimal("100000.00"),
        )
        PayrollEntry.objects.create(
            run=run,
            employee=self.employee,
            gross_pay=Decimal("100000.00"),
            net_pay=Decimal("100000.00"),
        )

        response = self.client.get(
            f"/api/payroll/organizations/{self.organization.id}/payroll/my-entries/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["period_name"], "September 2026")

    def test_me_exposes_membership_permissions(self):
        data = MeSerializer(self.user).data
        self.assertEqual(data["memberships"][0]["organization_id"], str(self.organization.id))
        self.assertIn("payroll.process", data["memberships"][0]["permissions"])
        self.assertFalse(data["is_hr_admin"])
        self.assertTrue(data["is_payroll_admin"])
