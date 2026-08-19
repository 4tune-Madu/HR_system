from datetime import date

from django.test import TestCase

from apps.employee.models import (
    Employee,
    EmployeeAssignment,
    EmployeeContact,
    EmployeeIdentity,
    Employment,
)
from apps.employee.services import (
    EmployeeService,
)

from apps.organization.models import (
    Department,
    JobGrade,
    Organization,
    Position,
    Team,
    Branch
)


class EmployeeServiceTests(TestCase):

    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
        )

        self.department = Department.objects.create(
            organization=self.organization,
            name="Engineering",
            code="ENG",
        )

        self.job_grade = JobGrade.objects.create(
            organization=self.organization,
            name="Senior",
            code="SEN",
            level=3,
        )

        self.position = Position.objects.create(
            organization=self.organization,
            department=self.department,
            job_grade=self.job_grade,
            title="Senior Software Engineer",
            code="SSE",
        )

        
    def test_create_employee(self):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            middle_name="Michael",
            last_name="Doe",
            date_of_birth=date(1995, 5, 10),
            gender="Male",
            personal_email="john@example.com",
            company_email="john.doe@testcompany.com",
            phone_number="08012345678",
            address="Lagos, Nigeria",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
            employment_type=Employment.EmploymentType.PERMANENT,
            employment_status=Employment.EmploymentStatus.PROBATION,
            offer_date=date(2026, 1, 5),
            employment_start_date=date(2026, 1, 12),
            probation_end_date=date(2026, 7, 12),
        )

        self.assertIsNotNone(employee)

        self.assertEqual(
            employee.organization,
            self.organization,
        )

        self.assertEqual(
            employee.employee_number,
            "EMP-000001",
        )

        identity = EmployeeIdentity.objects.get(
            employee=employee
        )

        self.assertEqual(
            identity.first_name,
            "John",
        )

        self.assertEqual(
            identity.last_name,
            "Doe",
        )

        contact = EmployeeContact.objects.get(
            employee=employee
        )

        self.assertEqual(
            contact.company_email,
            "john.doe@testcompany.com",
        )

        assignment = EmployeeAssignment.objects.get(
            employee=employee
        )

        self.assertEqual(
            assignment.department,
            self.department,
        )

        self.assertEqual(
            assignment.position,
            self.position,
        )

        employment = Employment.objects.get(
            employee=employee
        )

        self.assertEqual(
            employment.employment_status,
            Employment.EmploymentStatus.PROBATION,
        )

        self.assertEqual(
            employment.confirmation_status,
            Employment.ConfirmationStatus.PENDING,
        )

    def test_employee_number_generation(self):
        first_employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
        )

        second_employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="Jane",
            last_name="Doe",
        )

        self.assertEqual(
            first_employee.employee_number,
            "EMP-000001",
        )

        self.assertEqual(
            second_employee.employee_number,
            "EMP-000002",
        )


    def test_assignment_must_belong_to_employee_organization(self):
        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_department = Department.objects.create(
            organization=another_organization,
            name="Finance",
            code="FIN",
        )

        with self.assertRaises(ValueError):
            EmployeeService.create_employee(
                organization=self.organization,
                first_name="John",
                last_name="Doe",
                department=another_department,
            )

    def test_add_next_of_kin(self):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
        )

        next_of_kin = EmployeeService.add_next_of_kin(
            employee=employee,
            full_name="Mary Doe",
            relationship="Mother",
            phone_number="08012345678",
            is_primary=True,
        )

        self.assertEqual(
            next_of_kin.employee,
            employee,
        )

        self.assertTrue(
            next_of_kin.is_primary,
        )

    def test_only_one_primary_next_of_kin(self):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
        )

        first = EmployeeService.add_next_of_kin(
            employee=employee,
            full_name="Mary Doe",
            relationship="Mother",
            phone_number="08011111111",
            is_primary=True,
        )

        second = EmployeeService.add_next_of_kin(
            employee=employee,
            full_name="James Doe",
            relationship="Brother",
            phone_number="08022222222",
            is_primary=True,
        )

        first.refresh_from_db()

        self.assertFalse(first.is_primary)
        self.assertTrue(second.is_primary)

    def test_add_emergency_contact(self):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
        )

        contact = EmployeeService.add_emergency_contact(
            employee=employee,
            full_name="Mary Doe",
            relationship="Mother",
            phone_number="08012345678",
            is_primary=True,
        )

        self.assertEqual(
            contact.employee,
            employee,
        )

        self.assertTrue(
            contact.is_primary,
        )

    def test_list_employees(self):
        EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
        )

        EmployeeService.create_employee(
            organization=self.organization,
            first_name="Jane",
            last_name="Doe",
        )

        employees = EmployeeService.list_employees(
            organization=self.organization,
        )

        self.assertEqual(
            employees.count(),
            2,
        )

    def test_get_employee(self):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
        )

        result = EmployeeService.get_employee(
            employee_id=employee.id,
            organization=self.organization,
        )

        self.assertEqual(
            result.id,
            employee.id,
        )

    def test_employee_cannot_be_retrieved_from_wrong_organization(self):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
        )

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        with self.assertRaises(Employee.DoesNotExist):
            EmployeeService.get_employee(
                employee_id=employee.id,
                organization=another_organization,
            )

    def test_update_employee_identity(self):
    
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
        )
    
        updated_employee = EmployeeService.update_employee(
            employee=employee,
            identity_data={
                "first_name": "Michael",
                "last_name": "Doe",
            },
        )
    
        updated_employee.refresh_from_db()
    
        self.assertEqual(
            updated_employee.identity.first_name,
            "Michael",
        )
    
        self.assertEqual(
            updated_employee.identity.last_name,
            "Doe",
        )

    def test_update_employee_contact(self):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
        )

        EmployeeService.update_employee(
            employee=employee,
            contact_data={
                "phone_number": "08012345678",
            },
        )

        employee.refresh_from_db()

        self.assertEqual(
            employee.contact.phone_number,
            "08012345678",
        )

    def test_update_employee_employment(self):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
        )

        EmployeeService.update_employee(
            employee=employee,
            employment_data={
                "confirmation_status": (
                    Employment.ConfirmationStatus.CONFIRMED
                ),
                "confirmation_date": "2026-08-17",
            },
        )

        employee.refresh_from_db()

        self.assertEqual(
            employee.employment.confirmation_status,
            Employment.ConfirmationStatus.CONFIRMED,
        )

        self.assertEqual(
            str(
                employee.employment.confirmation_date
            ),
            "2026-08-17",
        )

    def test_update_department_from_another_organization_is_rejected(
        self,
    ):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
        )

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_department = Department.objects.create(
            organization=another_organization,
            name="Finance",
            code="FIN",
        )

        with self.assertRaises(ValueError):

            EmployeeService.update_employee(
                employee=employee,
                assignment_data={
                    "department": another_department,
                },
            )

    def test_update_position_from_another_organization_is_rejected(
        self,
    ):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
        )

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_position = Position.objects.create(
            organization=another_organization,
            title="Finance Manager",
            code="FM",
        )

        with self.assertRaises(ValueError):

            EmployeeService.update_employee(
                employee=employee,
                assignment_data={
                    "position": another_position,
                },
            )

    def test_update_job_grade_from_another_organization_is_rejected(
        self,
    ):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
        )

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_job_grade = JobGrade.objects.create(
            organization=another_organization,
            name="Manager",
            code="MGR",
            level=5,
        )

        with self.assertRaises(ValueError):

            EmployeeService.update_employee(
                employee=employee,
                assignment_data={
                    "job_grade": another_job_grade,
                },
            )


    def test_update_branch_from_another_organization_is_rejected(
        self,
    ):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
        )

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_branch = Branch.objects.create(
            organization=another_organization,
            name="Another Branch",
        )

        with self.assertRaises(ValueError):

            EmployeeService.update_employee(
                employee=employee,
                assignment_data={
                    "branch": another_branch,
                },
            )

    def test_update_team_from_another_organization_is_rejected(
        self,
    ):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
        )
    
        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )
    
        another_department = Department.objects.create(
            organization=another_organization,
            name="Finance",
            code="FIN",
        )
    
        another_team = Team.objects.create(
            department=another_department,
            name="Finance Team",
        )
    
        with self.assertRaises(ValueError):
        
            EmployeeService.update_employee(
                employee=employee,
                assignment_data={
                    "team": another_team,
                },
            )
    
    def test_update_manager_from_another_organization_is_rejected(
        self,
    ):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
        )

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_manager = EmployeeService.create_employee(
            organization=another_organization,
            first_name="Jane",
            last_name="Smith",
        )

        with self.assertRaises(ValueError):

            EmployeeService.update_employee(
                employee=employee,
                assignment_data={
                    "manager": another_manager,
                },
            )

    def test_update_department_same_organization_is_allowed(
        self,
    ):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
        )

        new_department = Department.objects.create(
            organization=self.organization,
            name="Finance",
            code="FIN",
        )

        EmployeeService.update_employee(
            employee=employee,
            assignment_data={
                "department": new_department,
            },
        )

        employee.refresh_from_db()

        self.assertEqual(
            employee.assignment.department,
            new_department,
        )