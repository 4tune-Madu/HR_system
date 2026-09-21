import uuid

from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase
from rest_framework import status

from apps.employee.services import (
    EmployeeService,
)

from apps.organization.models import (
    Organization,
    Department,
    Position,
    JobGrade,
    Team,
    Branch,
)

from apps.access.models import (
    Permission,
    Role,
    OrganizationMembership,
)

from apps.access.services import (
    RoleService,
    AccessService,
)

User = get_user_model()

from apps.employee.models import (
    Employee,
    EmployeeDocument,
)


from django.core.files.uploadedfile import SimpleUploadedFile


class EmployeeAPITests(APITestCase):

    def setUp(self):

        # -----------------------------------
        # Organization
        # -----------------------------------

        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
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

        self.role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="ORGANIZATION_ADMIN",
        )

        # -----------------------------------
        # Organization Membership
        # -----------------------------------

        self.membership = AccessService.assign_role(
            user=self.user,
            organization=self.organization,
            role=self.role,
        )

        # -----------------------------------
        # Department
        # -----------------------------------

        self.department = Department.objects.create(
            organization=self.organization,
            name="Engineering",
            code="ENG",
        )

        # -----------------------------------
        # Job Grade
        # -----------------------------------

        self.job_grade = JobGrade.objects.create(
            organization=self.organization,
            name="Senior",
            code="SEN",
            level=3,
        )

        # -----------------------------------
        # Position
        # -----------------------------------

        self.position = Position.objects.create(
            organization=self.organization,
            department=self.department,
            job_grade=self.job_grade,
            title="Senior Software Engineer",
            code="SSE",
        )

        # -----------------------------------
        # Existing Employee
        # -----------------------------------

        self.employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
            user=self.user,
        )

        # -----------------------------------
        # Authenticate
        # -----------------------------------

        self.client.force_authenticate(
            user=self.user,
        )

        # -----------------------------------
        # Organization-scoped URL
        # -----------------------------------

        self.employee_url = (
            f"/api/organizations/"
            f"{self.organization.id}/employees/"
        )


    def employee_list_url(self):
        return (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/"
        )


    def employee_detail_url(self, employee_id):
        return (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{employee_id}/"
        )


    # =======================================
    # GET EMPLOYEES
    # =======================================

    def test_list_employees(self):

        response = self.client.get(
            self.employee_list_url()
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
            response.data[0]["employee_number"],
            self.employee.employee_number,
        )

    # =======================================
    # GET NONEXISTENT EMPLOYEE
    # =======================================

    def test_get_nonexistent_employee(self):

        response = self.client.get(
            f"{self.employee_url}"
            f"{uuid.uuid4()}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # =======================================
    # CREATE EMPLOYEE
    # =======================================

    def test_create_employee(self):

        payload = {

            "identity": {
                "first_name": "Jane",
                "middle_name": "Mary",
                "last_name": "Smith",
                "date_of_birth": "1998-03-15",
                "gender": "Female",
            },

            "contact": {
                "personal_email": "jane@gmail.com",
                "company_email": (
                    "jane.smith@testcompany.com"
                ),
                "phone_number": "08012345678",
                "address": "Lagos, Nigeria",
            },

            "assignment": {
                "department": str(
                    self.department.id
                ),

                "position": str(
                    self.position.id
                ),

                "job_grade": str(
                    self.job_grade.id
                ),
            },

            "employment": {
                "employment_type": "PERMANENT",
                "employment_status": "PROBATION",
                "offer_date": "2026-08-01",
                "employment_start_date": "2026-08-11",
                "probation_end_date": "2027-02-11",
            },
        }

        response = self.client.post(
            self.employee_list_url(),
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["employee_number"],
            "EMP-000002",
        )

    # =======================================
    # CREATE EMPLOYEE REQUIRES IDENTITY
    # =======================================

    def test_create_employee_requires_identity(self):

        payload = {}

        response = self.client.post(
            self.employee_list_url(),
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # =======================================
    # CROSS-ORGANIZATION ASSIGNMENT
    # =======================================

    def test_assignment_from_another_organization_is_rejected(self):

        another_organization = (
            Organization.objects.create(
                name="Another Company",
                legal_name="Another Company Limited",
            )
        )

        another_department = (
            Department.objects.create(
                organization=another_organization,
                name="Finance",
                code="FIN",
            )
        )

        payload = {

            "identity": {
                "first_name": "Jane",
                "last_name": "Smith",
            },

            "assignment": {
                "department": str(
                    another_department.id
                ),
            },
        }

        response = self.client.post(
            self.employee_list_url(),
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_viewer_can_list_employees(self):

        viewer = User.objects.create_user(
            email="viewer@testcompany.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="Viewer",
        )

        viewer_role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="VIEWER",
        )

        AccessService.assign_role(
            user=viewer,
            organization=self.organization,
            role=viewer_role,
        )

        self.client.force_authenticate(
            user=viewer
        )

        response = self.client.get(
            self.employee_list_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_viewer_cannot_create_employee(self):

        viewer = User.objects.create_user(
            email="viewer2@testcompany.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="Viewer",
        )

        viewer_role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="VIEWER",
        )

        AccessService.assign_role(
            user=viewer,
            organization=self.organization,
            role=viewer_role,
        )

        self.client.force_authenticate(
            user=viewer
        )

        payload = {
            "identity": {
                "first_name": "Jane",
                "last_name": "Smith",
            },
        }

        response = self.client.post(
            self.employee_list_url(),
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


    def test_user_without_membership_cannot_list_employees(self):

        user = User.objects.create_user(
            email="outsider@testcompany.com",
            password="TestPassword123!",
            first_name="Outside",
            last_name="User",
        )

        self.client.force_authenticate(
            user=user
        )

        response = self.client.get(
            self.employee_list_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


    def test_inactive_membership_cannot_list_employees(self):

        user = User.objects.create_user(
            email="inactive@testcompany.com",
            password="TestPassword123!",
            first_name="Inactive",
            last_name="User",
        )

        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="VIEWER",
        )

        OrganizationMembership.objects.create(
            user=user,
            organization=self.organization,
            role=role,
            is_active=False,
        )

        self.client.force_authenticate(
            user=user
        )

        response = self.client.get(
            self.employee_list_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_user_cannot_access_another_organization(self):

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        response = self.client.get(
            f"/api/employees/"
            f"organizations/{another_organization.id}/"
            f"employees/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_get_employee(self):

        response = self.client.get(
            f"{self.employee_list_url()}"
            f"{self.employee.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["employee_number"],
            self.employee.employee_number,
        )


    def test_cannot_get_employee_from_another_organization(self):

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_employee = EmployeeService.create_employee(
            organization=another_organization,
            first_name="Jane",
            last_name="Smith",
            company_email="jane@anothercompany.com",
        )

        response = self.client.get(
            f"{self.employee_url}"
            f"{another_employee.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_update_employee_identity(self):

        response = self.client.patch(
            f"/api/employees/organizations/"
            f"{self.organization.id}/employees/"
            f"{self.employee.id}/",
            {
                "identity": {
                    "first_name": "Updated",
                    "last_name": "Employee",
                }
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.employee.identity.refresh_from_db()

        self.assertEqual(
            self.employee.identity.first_name,
            "Updated",
        )

    def test_deactivate_employee(self):

        user = User.objects.create_user(
            email="deactivate.admin@testcompany.com",
            password="TestPassword123!",
            first_name="Deactivate",
            last_name="Admin",
        )

        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="HR_MANAGER",
        )

        AccessService.assign_role(
            user=user,
            organization=self.organization,
            role=role,
        )

        self.client.force_authenticate(
            user=user
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
        )

        response = self.client.post(
            url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.employee.refresh_from_db()

        self.assertFalse(
            self.employee.is_active
        )

        self.assertFalse(
            response.data["is_active"]
        )


    def test_deactivate_already_inactive_employee(self):

        user = User.objects.create_user(
            email="inactive.admin@testcompany.com",
            password="TestPassword123!",
            first_name="Inactive",
            last_name="Admin",
        )

        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="HR_MANAGER",
        )

        AccessService.assign_role(
            user=user,
            organization=self.organization,
            role=role,
        )

        self.client.force_authenticate(
            user=user
        )

        self.employee.is_active = False
        self.employee.save()

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
        )

        response = self.client.post(
            url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["detail"],
            "Employee is already inactive.",
        )


    def test_viewer_cannot_deactivate_employee(self):

        user = User.objects.create_user(
            email="viewer@testcompany.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="Viewer",
        )

        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="VIEWER",
        )

        AccessService.assign_role(
            user=user,
            organization=self.organization,
            role=role,
        )

        self.client.force_authenticate(
            user=user
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
        )

        response = self.client.post(
            url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.employee.refresh_from_db()

        self.assertTrue(
            self.employee.is_active
        )


    def test_cannot_deactivate_employee_from_another_organization(self):

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        user = User.objects.create_user(
            email="another.admin@testcompany.com",
            password="TestPassword123!",
            first_name="Another",
            last_name="Admin",
        )

        role = RoleService.provision_system_role(
            organization=another_organization,
            role_code="HR_MANAGER",
        )

        AccessService.assign_role(
            user=user,
            organization=another_organization,
            role=role,
        )

        another_employee = EmployeeService.create_employee(
            organization=another_organization,
            first_name="Jane",
            last_name="Smith",
            company_email="jane@anothercompany.com",
        )

        self.client.force_authenticate(
            user=user
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
        )

        response = self.client.post(
            url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.employee.refresh_from_db()

        self.assertTrue(
            self.employee.is_active
        )

    def get_employee_document_url(
        self,
        employee=None,
        document_id=None,
    ):
        employee = employee or self.employee
     
        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{employee.id}/"
            f"documents/"
        )

        if document_id:
            url += f"{document_id}/"

        return url

    def create_test_document(
        self,
        employee=None,
    ):
        employee = employee or self.employee

        file = SimpleUploadedFile(
            "contract.pdf",
            b"test contract content",
            content_type="application/pdf",
        )

        return EmployeeDocument.objects.create(
            employee=employee,
            document_type=(
                EmployeeDocument
                .DocumentType
                .CONTRACT
            ),
            name="Employment Contract",
            file=file,
            description="Test employment contract",
        )

    def test_list_employee_documents(self):

        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="ORGANIZATION_ADMIN",
        )

        AccessService.assign_role(
            user=self.user,
            organization=self.organization,
            role=role,
        )

        self.create_test_document()

        url = self.get_employee_document_url()

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["name"],
            "Employment Contract",
        )

    def test_list_employee_documents(self):

        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="ORGANIZATION_ADMIN",
        )

        AccessService.assign_role(
            user=self.user,
            organization=self.organization,
            role=role,
        )

        self.create_test_document()

        url = self.get_employee_document_url()

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["name"],
            "Employment Contract",
        )

    def test_upload_employee_document(self):

        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="ORGANIZATION_ADMIN",
        )

        AccessService.assign_role(
            user=self.user,
            organization=self.organization,
            role=role,
        )

        file = SimpleUploadedFile(
            "certificate.pdf",
            b"certificate content",
            content_type="application/pdf",
        )

        url = self.get_employee_document_url()

        response = self.client.post(
            url,
            {
                "document_type": "CERTIFICATE",
                "name": "Professional Certificate",
                "file": file,
                "description": "Test certificate",
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["name"],
            "Professional Certificate",
        )

        self.assertTrue(
            EmployeeDocument.objects.filter(
                employee=self.employee,
                name="Professional Certificate",
            ).exists()
        )

    def test_viewer_cannot_upload_employee_document(self):

        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="VIEWER",
        )

        AccessService.assign_role(
            user=self.user,
            organization=self.organization,
            role=role,
        )

        file = SimpleUploadedFile(
            "certificate.pdf",
            b"certificate content",
            content_type="application/pdf",
        )

        url = self.get_employee_document_url()

        response = self.client.post(
            url,
            {
                "document_type": "CERTIFICATE",
                "name": "Professional Certificate",
                "file": file,
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_user_without_document_permission_cannot_list_documents(self):

        role = Role.objects.create(
            organization=self.organization,
            name="Employee Viewer",
            code="EMPLOYEE_VIEWER",
        )

        employee_view_permission = (
            Permission.objects.get(
                code="employee.view"
            )
        )

        role.permissions.add(
            employee_view_permission
        )

        AccessService.assign_role(
            user=self.user,
            organization=self.organization,
            role=role,
        )

        self.create_test_document()

        url = self.get_employee_document_url()

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_get_nonexistent_employee_document(self):

        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="ORGANIZATION_ADMIN",
        )

        AccessService.assign_role(
            user=self.user,
            organization=self.organization,
            role=role,
        )

        import uuid

        url = self.get_employee_document_url(
            document_id=uuid.uuid4(),
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(
            response.data["detail"],
            "Document not found.",
        )

    def test_cannot_access_another_employee_document(self):

        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="ORGANIZATION_ADMIN",
        )

        AccessService.assign_role(
            user=self.user,
            organization=self.organization,
            role=role,
        )

        another_employee = (
            EmployeeService.create_employee(
                organization=self.organization,
                first_name="Jane",
                last_name="Smith",
                company_email="jane@testcompany.com",
            )
        )

        document = self.create_test_document(
            employee=another_employee,
        )

        url = self.get_employee_document_url(
            employee=self.employee,
            document_id=document.id,
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_cannot_access_document_from_another_organization(self):

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_user = User.objects.create_user(
            email="another.document@testcompany.com",
            password="TestPassword123!",
            first_name="Another",
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

        another_employee = (
            EmployeeService.create_employee(
                organization=another_organization,
                first_name="Jane",
                last_name="Smith",
                company_email="jane@anothercompany.com",
            )
        )

        document = self.create_test_document(
            employee=another_employee,
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{another_employee.id}/"
            f"documents/{document.id}/"
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_archive_employee_document(self):

        document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Certificate",
            file=SimpleUploadedFile(
                "certificate.pdf",
                b"test document",
                content_type="application/pdf",
            ),
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"documents/{document.id}/"
        )

        response = self.client.delete(
            url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        document.refresh_from_db()

        # Document should be archived
        self.assertTrue(
            document.is_archived
        )

        # Archive timestamp should exist
        self.assertIsNotNone(
            document.archived_at
        )

        # Database record must still exist
        self.assertTrue(
            EmployeeDocument.objects.filter(
                id=document.id
            ).exists()
        )

    def test_archived_document_cannot_be_retrieved(self):

        document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Certificate",
            file=SimpleUploadedFile(
                "certificate.pdf",
                b"test document",
                content_type="application/pdf",
            ),
        )

        document.is_archived = True
        document.archived_at = timezone.now()
        document.save()

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"documents/{document.id}/"
        )

        response = self.client.get(
            url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_archive_already_archived_document(self):

        document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Certificate",
            file=SimpleUploadedFile(
                "certificate.pdf",
                b"test document",
                content_type="application/pdf",
            ),
            is_archived=True,
            archived_at=timezone.now(),
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"documents/{document.id}/"
        )

        response = self.client.delete(
            url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_viewer_cannot_archive_employee_document(self):

        viewer = User.objects.create_user(
            email="document.viewer@testcompany.com",
            password="TestPassword123!",
            first_name="Document",
            last_name="Viewer",
        )

        viewer_role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="VIEWER",
        )

        AccessService.assign_role(
            user=viewer,
            organization=self.organization,
            role=viewer_role,
        )

        document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Certificate",
            file=SimpleUploadedFile(
                "certificate.pdf",
                b"test document",
                content_type="application/pdf",
            ),
        )

        self.client.force_authenticate(
            user=viewer
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"documents/{document.id}/"
        )

        response = self.client.delete(
            url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        document.refresh_from_db()

        self.assertFalse(
            document.is_archived
        )

    def test_list_archived_employee_documents(self):

        document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Archived Certificate",
            file=SimpleUploadedFile(
                "certificate.pdf",
                b"test document",
                content_type="application/pdf",
            ),
            is_archived=True,
            archived_at=timezone.now(),
            archived_by=self.user,
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"documents/archived/"
        )

        response = self.client.get(
            url
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
            str(response.data[0]["id"]),
            str(document.id),
        )

        self.assertTrue(
            response.data[0]["is_archived"]
        )

        self.assertEqual(
            str(response.data[0]["archived_by"]),
            str(self.user.id),
        )

    def test_active_document_list_excludes_archived_documents(self):

        active_document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Active Certificate",
            file=SimpleUploadedFile(
                "active.pdf",
                b"active document",
                content_type="application/pdf",
            ),
        )

        archived_document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Archived Certificate",
            file=SimpleUploadedFile(
                "archived.pdf",
                b"archived document",
                content_type="application/pdf",
            ),
            is_archived=True,
            archived_at=timezone.now(),
            archived_by=self.user,
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"documents/"
        )


    def test_active_document_list_excludes_archived_documents(self):

        active_document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Active Certificate",
            file=SimpleUploadedFile(
                "active.pdf",
                b"active document",
                content_type="application/pdf",
            ),
        )

        archived_document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Archived Certificate",
            file=SimpleUploadedFile(
                "archived.pdf",
                b"archived document",
                content_type="application/pdf",
            ),
            is_archived=True,
            archived_at=timezone.now(),
            archived_by=self.user,
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"documents/"
        )

    def test_restore_employee_document(self):

        document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Archived Certificate",
            file=SimpleUploadedFile(
                "certificate.pdf",
                b"test document",
                content_type="application/pdf",
            ),
            is_archived=True,
            archived_at=timezone.now(),
            archived_by=self.user,
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"documents/{document.id}/restore/"
        )

        response = self.client.post(
            url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        document.refresh_from_db()

        self.assertFalse(
            document.is_archived
        )

        self.assertIsNone(
            document.archived_at
        )

        self.assertIsNone(
            document.archived_by
        )

    def test_restore_active_employee_document_fails(self):

        document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Active Certificate",
            file=SimpleUploadedFile(
                "certificate.pdf",
                b"test document",
                content_type="application/pdf",
            ),
            is_archived=False,
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"documents/{document.id}/restore/"
        )

        response = self.client.post(
            url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        document.refresh_from_db()

        self.assertFalse(
            document.is_archived
        )

    def test_viewer_cannot_restore_employee_document(self):

        viewer = User.objects.create_user(
            email="restore.viewer@testcompany.com",
            password="TestPassword123!",
            first_name="Restore",
            last_name="Viewer",
        )

        viewer_role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="VIEWER",
        )

        AccessService.assign_role(
            user=viewer,
            organization=self.organization,
            role=viewer_role,
        )

        document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Archived Certificate",
            file=SimpleUploadedFile(
                "certificate.pdf",
                b"test document",
                content_type="application/pdf",
            ),
            is_archived=True,
            archived_at=timezone.now(),
            archived_by=self.user,
        )

        self.client.force_authenticate(
            user=viewer
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"documents/{document.id}/restore/"
        )

        response = self.client.post(
            url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        document.refresh_from_db()

        self.assertTrue(
            document.is_archived
        )

    def test_cannot_restore_document_from_another_organization(self):

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_employee = EmployeeService.create_employee(
            organization=another_organization,
            first_name="Jane",
            last_name="Smith",
            company_email="jane@anothercompany.com",
        )

        document = EmployeeDocument.objects.create(
            employee=another_employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Another Certificate",
            file=SimpleUploadedFile(
                "certificate.pdf",
                b"test document",
                content_type="application/pdf",
            ),
            is_archived=True,
            archived_at=timezone.now(),
            archived_by=self.user,
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{another_employee.id}/"
            f"documents/{document.id}/restore/"
        )

        response = self.client.post(
            url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        document.refresh_from_db()

        self.assertTrue(
            document.is_archived
        )

    def test_restored_document_appears_in_active_document_list(self):

        document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type=EmployeeDocument.DocumentType.CERTIFICATE,
            name="Archived Certificate",
            file=SimpleUploadedFile(
                "certificate.pdf",
                b"test document",
                content_type="application/pdf",
            ),
            is_archived=True,
            archived_at=timezone.now(),
            archived_by=self.user,
        )

        restore_url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"documents/{document.id}/restore/"
        )

        response = self.client.post(
            restore_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        list_url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
            f"documents/"
        )

        response = self.client.get(
            list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        document_ids = [
            item["id"]
            for item in response.data
        ]

        self.assertIn(
            str(document.id),
            document_ids,
        )

    def test_provision_employee_account_api(self):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="Jane",
            last_name="Smith",
            company_email="jane.smith@testcompany.com",
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{employee.id}/"
            f"account/provision/"
        )

        response = self.client.post(
            url,
            {
                "role_code": "EMPLOYEE",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        employee.refresh_from_db()

        self.assertIsNotNone(
            employee.user_id,
        )

        self.assertEqual(
            employee.user.email,
            "jane.smith@testcompany.com",
        )

        self.assertFalse(
            employee.user.has_usable_password(),
        )

    def test_viewer_cannot_provision_employee_account(self):

        viewer = User.objects.create_user(
            email="provision.viewer@testcompany.com",
            password="TestPassword123!",
            first_name="Provision",
            last_name="Viewer",
        )

        viewer_role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="VIEWER",
        )

        AccessService.assign_role(
            user=viewer,
            organization=self.organization,
            role=viewer_role,
        )

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="Jane",
            last_name="Smith",
            company_email="jane.smith@testcompany.com",
        )

        self.client.force_authenticate(
            user=viewer,
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{employee.id}/"
            f"account/provision/"
        )

        response = self.client.post(
            url,
            {
                "role_code": "EMPLOYEE",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        employee.refresh_from_db()

        self.assertIsNone(
            employee.user_id,
        )

    def test_provision_employee_account_api_twice(self):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="Jane",
            last_name="Smith",
            company_email="jane.smith@testcompany.com",
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{employee.id}/"
            f"account/provision/"
        )

        first_response = self.client.post(
            url,
            {
                "role_code": "EMPLOYEE",
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        second_response = self.client.post(
            url,
            {
                "role_code": "EMPLOYEE",
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_cannot_provision_account_for_another_organization_employee(
        self,
    ):

        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )

        another_employee = EmployeeService.create_employee(
            organization=another_organization,
            first_name="Jane",
            last_name="Smith",
            company_email="jane@anothercompany.com",
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{another_employee.id}/"
            f"account/provision/"
        )

        response = self.client.post(
            url,
            {
                "role_code": "EMPLOYEE",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        another_employee.refresh_from_db()

        self.assertIsNone(
            another_employee.user_id,
        )


    def test_invite_employee_account(self):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="Jane",
            last_name="Smith",
            company_email="jane.smith@testcompany.com",
        )

        EmployeeService.provision_employee_account(
            employee=employee,
            role_code="EMPLOYEE",
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{employee.id}/"
            f"account/invite/"
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["detail"],
            "Invitation sent successfully.",
        )


    def test_cannot_invite_employee_without_account(self):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="Jane",
            last_name="Smith",
            company_email="jane.smith@testcompany.com",
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{employee.id}/"
            f"account/invite/"
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_cannot_invite_account_after_password_setup(
        self,
    ):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="Jane",
            last_name="Smith",
            company_email="jane.smith@testcompany.com",
        )

        result = (
            EmployeeService
            .provision_employee_account(
                employee=employee,
                role_code="EMPLOYEE",
            )
        )

        user = result["user"]

        user.set_password(
            "ExistingPassword123!"
        )

        user.password_reset_required = False

        user.save(
            update_fields=[
                "password",
                "password_reset_required",
            ]
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{employee.id}/"
            f"account/invite/"
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_viewer_cannot_invite_employee_account(
        self,
    ):

        viewer = User.objects.create_user(
            email="viewer@testcompany.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="Viewer",
        )

        role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="VIEWER",
        )

        AccessService.assign_role(
            user=viewer,
            organization=self.organization,
            role=role,
        )

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="Jane",
            last_name="Smith",
            company_email="jane.smith@testcompany.com",
        )

        EmployeeService.provision_employee_account(
            employee=employee,
            role_code="EMPLOYEE",
        )

        self.client.force_authenticate(
            user=viewer,
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{employee.id}/"
            f"account/invite/"
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_activate_employee_api(self):

        employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="Jane",
            last_name="Smith",
            company_email="jane.smith@testcompany.com",
        )

        EmployeeService.deactivate_employee(
            employee=employee,
        )

        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{employee.id}/"
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

        employee.refresh_from_db()

        self.assertTrue(
            employee.is_active,
        )

    def test_activate_active_employee_api(
        self,
    ):
    
        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
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
    
        self.assertEqual(
            response.data["detail"],
            "Employee is already active.",
        )
    
    def test_viewer_cannot_activate_employee(
        self,
    ):
    
        viewer = User.objects.create_user(
            email="activate.viewer@testcompany.com",
            password="TestPassword123!",
            first_name="Activate",
            last_name="Viewer",
        )
    
        viewer_role = RoleService.provision_system_role(
            organization=self.organization,
            role_code="VIEWER",
        )
    
        AccessService.assign_role(
            user=viewer,
            organization=self.organization,
            role=viewer_role,
        )
    
        EmployeeService.deactivate_employee(
            employee=self.employee,
        )
    
        self.client.force_authenticate(
            user=viewer,
        )
    
        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{self.employee.id}/"
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
    
        self.employee.refresh_from_db()
    
        self.assertFalse(
            self.employee.is_active
        )
    
    def test_cannot_activate_employee_from_another_organization(
        self,
    ):
    
        another_organization = Organization.objects.create(
            name="Another Company",
            legal_name="Another Company Limited",
        )
    
        another_employee = EmployeeService.create_employee(
            organization=another_organization,
            first_name="Jane",
            last_name="Smith",
            company_email="jane@anothercompany.com",
        )
    
        EmployeeService.deactivate_employee(
            employee=another_employee,
        )
    
        url = (
            f"/api/employees/"
            f"organizations/{self.organization.id}/"
            f"employees/{another_employee.id}/"
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
    
        another_employee.refresh_from_db()
    
        self.assertFalse(
            another_employee.is_active
        )