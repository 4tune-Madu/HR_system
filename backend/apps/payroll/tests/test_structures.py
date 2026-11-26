from datetime import date
from decimal import Decimal
from rest_framework.test import APITestCase
from apps.payroll.tests import test_api
from apps.payroll.models import SalaryStructure, PayrollPeriod, PayrollRun, EmployeeCompensation
from apps.organization.models import JobGrade, Position, Organization


class SalaryStructureTests(APITestCase):
    setUp = test_api.PayrollAPITests.setUp

    def setup_structure(self):
        self.grade = JobGrade.objects.create(organization=self.organization, name="Senior", code="G1", level=1)
        self.position = Position.objects.create(organization=self.organization, title="Engineer", code="ENG", job_grade=self.grade)
        assignment = self.employee.assignment
        assignment.position = self.position
        assignment.job_grade = self.grade
        assignment.save()
        self.structure = SalaryStructure.objects.create(organization=self.organization, job_grade=self.grade, monthly_base=Decimal("100000"), effective_from=date(2026, 1, 1), components=[{"name": "Transport", "kind": "EARNING", "amount": "15000"}, {"name": "Loan", "kind": "DEDUCTION", "amount": "5000"}])

    def process(self):
        period = PayrollPeriod.objects.create(organization=self.organization, name="October", start_date=date(2026, 10, 1), end_date=date(2026, 10, 31))
        return self.client.post(f"/api/payroll/organizations/{self.organization.id}/payroll/periods/{period.id}/process/")

    def test_grade_structure_and_components(self):
        self.setup_structure()
        response = self.process()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Decimal(response.data["total_net"]), Decimal("110000"))
        self.assertIn("Transport", response.data["entries"][0]["notes"])
        self.structure.monthly_base = 200000
        self.structure.save()
        self.assertEqual(PayrollRun.objects.get().total_net, Decimal("110000"))

    def test_position_overrides_grade_and_future_version_is_excluded(self):
        self.setup_structure()
        SalaryStructure.objects.create(organization=self.organization, position=self.position, monthly_base=200000, effective_from=date(2026, 1, 1))
        SalaryStructure.objects.create(organization=self.organization, position=self.position, monthly_base=300000, effective_from=date(2026, 11, 1))
        response = self.process()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Decimal(response.data["total_net"]), Decimal("200000"))

    def test_employee_override_is_not_double_counted_with_structure(self):
        self.setup_structure()
        EmployeeCompensation.objects.create(employee=self.employee, monthly_gross=120000, effective_from=date(2026, 1, 1))
        response = self.process()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Decimal(response.data["total_net"]), Decimal("120000"))

    def test_structure_api_validates_scope_components_and_duplicates(self):
        self.setup_structure()
        url = f"/api/payroll/organizations/{self.organization.id}/payroll/structures/"
        payload = {"position": str(self.position.id), "monthly_base": "150000", "effective_from": "2026-01-01", "components": [{"name": "Transport", "kind": "EARNING", "amount": "10000"}]}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 400)
        other = Organization.objects.create(name="Other")
        grade = JobGrade.objects.create(organization=other, code="G1", name="Other", level=1)
        self.assertEqual(self.client.post(url, {**payload, "position": None, "job_grade": str(grade.id)}, format="json").status_code, 400)
        self.assertEqual(self.client.post(url, {**payload, "components": [{"name": "Invalid", "kind": "EARNING", "amount": "-1"}]}, format="json").status_code, 400)

    def test_excess_deductions_roll_back_run(self):
        self.setup_structure()
        self.structure.components = [{"name": "Loan", "kind": "DEDUCTION", "amount": "200000"}]
        self.structure.save()
        self.assertEqual(self.process().status_code, 400)
        self.assertFalse(PayrollRun.objects.exists())
