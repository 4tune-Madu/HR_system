from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.access.services import AccessService, RoleService
from apps.accounts.models import User
from apps.employee.models import EmployeeDocument
from apps.employee.services import EmployeeService
from apps.organization.models import Organization


class EmployeeDocumentDownloadTests(APITestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        override = override_settings(MEDIA_ROOT=directory.name)
        override.enable()
        self.addCleanup(override.disable)
        self.organization = Organization.objects.create(name="Document QA", legal_name="Document QA")
        self.user = User.objects.create_user(email="documents@example.test", password="TestPassword123!")
        role = RoleService.provision_system_role(organization=self.organization, role_code="VIEWER")
        AccessService.assign_role(user=self.user, organization=self.organization, role=role)
        self.employee = EmployeeService.create_employee(
            organization=self.organization, first_name="Document", last_name="QA",
            company_email="employee@example.test",
        )
        self.document = EmployeeDocument.objects.create(
            employee=self.employee, document_type="OTHER", name="QA document",
            file=SimpleUploadedFile("qa.txt", b"Local QA file", content_type="text/plain"),
        )
        self.url = f"/api/employees/organizations/{self.organization.id}/employees/{self.employee.id}/documents/{self.document.id}/download/"
        self.client.force_authenticate(self.user)

    def test_authorized_download_returns_original_bytes(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment;', response["Content-Disposition"])
        self.assertEqual(b"".join(response.streaming_content), b"Local QA file")
        response.close()

    def test_unauthenticated_download_is_denied(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_role_without_document_permission_is_denied(self):
        role = RoleService.provision_system_role(organization=self.organization, role_code="MANAGER")
        AccessService.assign_role(user=self.user, organization=self.organization, role=role)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_document_cannot_be_downloaded_under_another_employee(self):
        employee = EmployeeService.create_employee(
            organization=self.organization, first_name="Other", last_name="QA",
            company_email="other@example.test",
        )
        url = self.url.replace(str(self.employee.id), str(employee.id))
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_document_cannot_be_downloaded_under_another_organization(self):
        organization = Organization.objects.create(name="Other QA", legal_name="Other QA")
        url = self.url.replace(str(self.organization.id), str(organization.id))
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_missing_file_returns_not_found(self):
        self.document.file.storage.delete(self.document.file.name)
        self.assertEqual(self.client.get(self.url).status_code, 404)
