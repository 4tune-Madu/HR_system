from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.access.models import OrganizationMembership
from apps.access.services import (
    AccessService,
    RoleService,
)

from apps.employee.services import EmployeeService

from apps.organization.models import (
    Organization,
    Department,
    JobGrade,
    Position,
)


User = get_user_model()


class EmployeeWebTests(TestCase):

    def setUp(self):

        # -----------------------------------
        # Organization
        # -----------------------------------

        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
        )

        # -----------------------------------
        # Organization Admin
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

        self.admin_membership = (
            AccessService.assign_role(
                user=self.admin_user,
                organization=self.organization,
                role=self.admin_role,
            )
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
        # Employee
        # -----------------------------------

        self.employee = EmployeeService.create_employee(
            organization=self.organization,
            first_name="John",
            last_name="Doe",
            company_email="john.doe@testcompany.com",
            department=self.department,
            position=self.position,
            job_grade=self.job_grade,
            user=None,
        )

    # =================================================
    # Helpers
    # =================================================

    def employee_list_url(self):
        return reverse(
            "employee:list",
            kwargs={
                "organization_id": self.organization.id,
            },
        )

    def employee_detail_url(self):
        return reverse(
            "employee:detail",
            kwargs={
                "organization_id": self.organization.id,
                "employee_id": self.employee.id,
            },
        )

    def employee_document_url(self):
        return reverse(
            "employee:document-list",
            kwargs={
                "organization_id": self.organization.id,
                "employee_id": self.employee.id,
            },
        )

    def employee_document_upload_url(self):
        return reverse(
            "employee:document-upload",
            kwargs={
                "organization_id": self.organization.id,
                "employee_id": self.employee.id,
            },
        )

    # =================================================
    # Authentication
    # =================================================

    def test_employee_list_requires_authentication(self):

        response = self.client.get(
            self.employee_list_url()
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    # =================================================
    # Employee list
    # =================================================

    def test_admin_can_view_employee_list(self):

        self.client.force_login(
            self.admin_user
        )

        response = self.client.get(
            self.employee_list_url()
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "employee/employees/list.html",
        )

        self.assertContains(
            response,
            "EMP-000001",
        )

        self.assertContains(
            response,
            "John",
        )

        self.assertContains(
            response,
            "Doe",
        )

    # =================================================
    # Employee detail
    # =================================================

    def test_admin_can_view_employee_detail(self):

        self.client.force_login(
            self.admin_user
        )

        response = self.client.get(
            self.employee_detail_url()
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "employee/employees/detail.html",
        )

        self.assertContains(
            response,
            "John",
        )

        self.assertContains(
            response,
            "Doe",
        )

        self.assertContains(
            response,
            "EMP-000001",
        )

    # =================================================
    # Viewer
    # =================================================

    def test_viewer_can_view_employee_list(self):

        viewer = User.objects.create_user(
            email="viewer@testcompany.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="Viewer",
        )

        viewer_role = (
            RoleService.provision_system_role(
                organization=self.organization,
                role_code="VIEWER",
            )
        )

        AccessService.assign_role(
            user=viewer,
            organization=self.organization,
            role=viewer_role,
        )

        self.client.force_login(
            viewer
        )

        response = self.client.get(
            self.employee_list_url()
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "employee/employees/list.html",
        )

    # =================================================
    # No membership
    # =================================================

    def test_user_without_membership_gets_403(self):

        user = User.objects.create_user(
            email="outsider@testcompany.com",
            password="TestPassword123!",
            first_name="Outside",
            last_name="User",
        )

        self.client.force_login(
            user
        )

        response = self.client.get(
            self.employee_list_url()
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    # =================================================
    # Inactive membership
    # =================================================

    def test_inactive_membership_gets_403(self):

        user = User.objects.create_user(
            email="inactive@testcompany.com",
            password="TestPassword123!",
            first_name="Inactive",
            last_name="User",
        )

        role = (
            RoleService.provision_system_role(
                organization=self.organization,
                role_code="VIEWER",
            )
        )

        OrganizationMembership.objects.create(
            user=user,
            organization=self.organization,
            role=role,
            is_active=False,
        )

        self.client.force_login(
            user
        )

        response = self.client.get(
            self.employee_list_url()
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    # =================================================
    # Wrong organization
    # =================================================

    def test_user_cannot_access_another_organization(self):

        another_organization = (
            Organization.objects.create(
                name="Another Company",
                legal_name="Another Company Limited",
            )
        )

        another_user = User.objects.create_user(
            email="another@testcompany.com",
            password="TestPassword123!",
            first_name="Another",
            last_name="User",
        )

        another_role = (
            RoleService.provision_system_role(
                organization=another_organization,
                role_code="ORGANIZATION_ADMIN",
            )
        )

        AccessService.assign_role(
            user=another_user,
            organization=another_organization,
            role=another_role,
        )

        self.client.force_login(
            another_user
        )

        response = self.client.get(
            self.employee_list_url()
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    # =================================================
    # Document upload permission
    # =================================================

    def test_admin_can_access_document_upload_page(self):

        self.client.force_login(
            self.admin_user
        )

        response = self.client.get(
            self.employee_document_upload_url()
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "employee/documents/upload.html",
        )

    # =================================================
    # Viewer cannot upload documents
    # =================================================

    def test_viewer_cannot_access_document_upload_page(self):

        viewer = User.objects.create_user(
            email="document.viewer@testcompany.com",
            password="TestPassword123!",
            first_name="Document",
            last_name="Viewer",
        )

        viewer_role = (
            RoleService.provision_system_role(
                organization=self.organization,
                role_code="VIEWER",
            )
        )

        AccessService.assign_role(
            user=viewer,
            organization=self.organization,
            role=viewer_role,
        )

        self.client.force_login(
            viewer
        )

        response = self.client.get(
            self.employee_document_upload_url()
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    # =================================================
    # Document list permission
    # =================================================

    def test_admin_can_view_documents(self):

        self.client.force_login(
            self.admin_user
        )

        response = self.client.get(
            self.employee_document_url()
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "employee/documents/list.html",
        )

    def test_viewer_can_view_documents(self):

        viewer = User.objects.create_user(
            email="document.viewer2@testcompany.com",
            password="TestPassword123!",
            first_name="Document",
            last_name="Viewer",
        )

        viewer_role = (
            RoleService.provision_system_role(
                organization=self.organization,
                role_code="VIEWER",
            )
        )

        AccessService.assign_role(
            user=viewer,
            organization=self.organization,
            role=viewer_role,
        )

        self.client.force_login(
            viewer
        )

        response = self.client.get(
            self.employee_document_url()
        )

        self.assertEqual(
            response.status_code,
            200,
        )