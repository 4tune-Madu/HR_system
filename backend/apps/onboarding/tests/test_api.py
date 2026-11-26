from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone

from apps.access.services import AccessService, RoleService
from apps.accounts.models import User
from apps.employee.services import EmployeeService
from apps.organization.models import Organization

from apps.onboarding.models import OnboardingTask


class OnboardingTaskAPITests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Onboarding Test Company", legal_name="Onboarding Test Company Limited")
        self.user = User.objects.create_user(email="hr@testcompany.com", password="TestPassword123!")
        role = RoleService.provision_system_role(organization=self.organization, role_code="HR_OFFICER")
        AccessService.assign_role(user=self.user, organization=self.organization, role=role)
        self.employee = EmployeeService.create_employee(organization=self.organization, first_name="Ada", last_name="Okafor", company_email="ada@testcompany.com")
        self.client.force_authenticate(user=self.user)

    def tasks_url(self):
        return f"/api/onboarding/organizations/{self.organization.id}/onboarding/tasks/"

    def test_hr_can_create_task_for_employee_in_their_organization(self):
        response = self.client.post(self.tasks_url(), {"employee": str(self.employee.id), "title": "Complete orientation", "due_date": "2026-10-20"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["employee_number"], self.employee.employee_number)

    def test_completing_task_sets_completion_timestamp(self):
        task = OnboardingTask.objects.create(organization=self.organization, employee=self.employee, title="Issue laptop")
        response = self.client.patch(f"{self.tasks_url()}{task.id}/", {"status": "COMPLETED"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertIsNotNone(task.completed_at)

    def test_reopening_task_clears_completion_timestamp(self):
        task = OnboardingTask.objects.create(organization=self.organization, employee=self.employee, title="Issue access", status="COMPLETED", completed_at=timezone.now())
        response = self.client.patch(f"{self.tasks_url()}{task.id}/", {"status": "TODO"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertIsNone(task.completed_at)
