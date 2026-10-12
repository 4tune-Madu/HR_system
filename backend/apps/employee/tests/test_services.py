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
    RoleService,
)

from apps.organization.models import (
    Department,
    JobGrade,
    Organization,
    Position,
    Team,
    Branch
)

from apps.access.models import (
    OrganizationMembership,
)

from apps.access.services import (
    AccessService,
)

from apps.accounts.models import User

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

    def test_provision_employee_account(self):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
        )

        result = EmployeeService.provision_employee_account(
            employee=employee,
            role_code="EMPLOYEE",
        )

        employee.refresh_from_db()
        user = result["user"]

        self.assertIsNotNone(
            employee.user,
        )

        self.assertEqual(
            employee.user_id,
            user.id,
        )

        self.assertEqual(
            user.email,
            "john.doe@testcompany.com",
        )

        self.assertEqual(
            user.first_name,
            "John",
        )

        self.assertEqual(
            user.last_name,
            "Doe",
        )

        self.assertFalse(
            user.has_usable_password(),
        )

        self.assertTrue(
            OrganizationMembership.objects.filter(
                user=user,
                organization=self.organization,
                is_active=True,
                role=result["role"],
            ).exists()
        )

    def test_cannot_provision_employee_account_twice(self):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
        )

        EmployeeService.provision_employee_account(
            employee=employee,
            role_code="EMPLOYEE",
        )

        with self.assertRaises(ValueError):
            EmployeeService.provision_employee_account(
                employee=employee,
                role_code="EMPLOYEE",
            )


    def test_provision_employee_account_requires_company_email(
        self,
    ):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
        )

        with self.assertRaises(ValueError) as context:

            EmployeeService.provision_employee_account(
                employee=employee,
                role_code="EMPLOYEE",
            )

        self.assertIn(
            "company email",
            str(context.exception).lower(),
        )

    def test_provision_employee_account_rejects_existing_email(
        self,
    ):

        User.objects.create_user(
            email="john.doe@testcompany.com",
            password="ExistingPassword123!",
            first_name="Existing",
            last_name="User",
        )

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
        )

        with self.assertRaises(ValueError):

            EmployeeService.provision_employee_account(
                employee=employee,
                role_code="EMPLOYEE",
            )


    def test_provision_employee_account_rejects_forbidden_role(
        self,
    ):
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
        )

        with self.assertRaises(ValueError) as context:
            EmployeeService.provision_employee_account(
                employee=employee,
                role_code="ORGANIZATION_ADMIN",
            )

        self.assertIn(
            "cannot be assigned",
            str(context.exception),
        )

        employee.refresh_from_db()

        self.assertIsNone(
            employee.user_id
        )

        self.assertFalse(
            User.objects.filter(
                email="john.doe@testcompany.com"
            ).exists()
        )

    def test_deactivate_employee_deactivates_account_access(
        self,
    ):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
        )

        result = (
            EmployeeService
            .provision_employee_account(
                employee=employee,
                role_code="EMPLOYEE",
            )
        )

        user = result["user"]

        employee.refresh_from_db()

        self.assertTrue(
            employee.is_active,
        )

        self.assertTrue(
            user.is_active,
        )

        self.assertTrue(
            OrganizationMembership.objects.filter(
                user=user,
                organization=self.organization,
                is_active=True,
            ).exists()
        )

        EmployeeService.deactivate_employee(
            employee=employee,
        )

        employee.refresh_from_db()
        user.refresh_from_db()

        self.assertFalse(
            employee.is_active,
        )

        self.assertFalse(
            user.is_active,
        )

        self.assertFalse(
            OrganizationMembership.objects.filter(
                user=user,
                organization=self.organization,
                is_active=True,
            ).exists()
        )

        # Relationship is preserved
        self.assertEqual(
            employee.user_id,
            user.id,
        )

    def test_deactivate_employee_does_not_disable_user_with_other_active_membership(
        self,
    ):

        another_organization = (
            Organization.objects.create(
                name="Another Company",
                legal_name="Another Company Limited",
            )
        )

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
        )

        result = (
            EmployeeService
            .provision_employee_account(
                employee=employee,
                role_code="EMPLOYEE",
            )
        )

        user = result["user"]

        another_role = (
            RoleService.provision_system_role(
                organization=another_organization,
                role_code="EMPLOYEE",
            )
        )

        AccessService.assign_role(
            user=user,
            organization=another_organization,
            role=another_role,
        )

        EmployeeService.deactivate_employee(
            employee=employee,
        )

        employee.refresh_from_db()
        user.refresh_from_db()

        self.assertFalse(
            employee.is_active,
        )

        self.assertTrue(
            user.is_active,
        )

        self.assertFalse(
            OrganizationMembership.objects.filter(
                user=user,
                organization=self.organization,
                is_active=True,
            ).exists()
        )

        self.assertTrue(
            OrganizationMembership.objects.filter(
                user=user,
                organization=another_organization,
                is_active=True,
            ).exists()
        )

    def test_activate_employee(self):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
        )

        result = (
            EmployeeService
            .provision_employee_account(
                employee=employee,
                role_code="EMPLOYEE",
            )
        )

        user = result["user"]

        EmployeeService.deactivate_employee(
            employee=employee,
        )

        employee.refresh_from_db()
        user.refresh_from_db()

        self.assertFalse(
            employee.is_active,
        )

        self.assertFalse(
            user.is_active,
        )

        EmployeeService.activate_employee(
            employee=employee,
        )

        employee.refresh_from_db()
        user.refresh_from_db()

        self.assertTrue(
            employee.is_active,
        )

        self.assertTrue(
            user.is_active,
        )

        self.assertTrue(
            OrganizationMembership.objects.filter(
                user=user,
                organization=self.organization,
                is_active=True,
            ).exists()
        )


    def test_cannot_activate_active_employee(self):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
        )

        with self.assertRaises(ValueError):
            EmployeeService.activate_employee(
                employee=employee,
            )

    def test_activate_employee_preserves_password_setup_requirement(
        self,
    ):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
        )

        result = (
            EmployeeService
            .provision_employee_account(
                employee=employee,
                role_code="EMPLOYEE",
            )
        )

        user = result["user"]

        self.assertTrue(
            user.password_reset_required
        )

        EmployeeService.deactivate_employee(
            employee=employee,
        )

        EmployeeService.activate_employee(
            employee=employee,
        )

        user.refresh_from_db()

        self.assertTrue(
            user.password_reset_required
        )

        self.assertFalse(
            user.has_usable_password()
        )

    def test_activate_employee_requires_organization_membership(
        self,
    ):
    
        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
        )
    
        result = EmployeeService.provision_employee_account(
            employee=employee,
            role_code="EMPLOYEE",
        )
    
        user = result["user"]
    
        OrganizationMembership.objects.filter(
            user=user,
            organization=self.organization,
        ).delete()
    
        EmployeeService.deactivate_employee(
            employee=employee,
        )
    
        with self.assertRaises(ValueError):
            EmployeeService.activate_employee(
                employee=employee,
            )