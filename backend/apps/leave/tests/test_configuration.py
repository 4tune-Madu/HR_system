from rest_framework.test import APITestCase
from apps.leave.tests import test_api
from apps.access.services import RoleService, AccessService
from apps.leave.models import LeaveBalance


class LeaveConfigurationTests(APITestCase):
    setUp = test_api.LeaveRequestAPITests.setUp

    def test_hr_manager_can_initialize_balances_without_resetting_used_days(self):
        role = RoleService.provision_system_role(organization=self.organization, role_code="HR_MANAGER")
        AccessService.assign_role(user=self.admin_user, organization=self.organization, role=role)
        self.client.force_authenticate(self.admin_user)
        self.balance.used_days = 5
        self.balance.save()
        url = f"/api/leave/organizations/{self.organization.id}/leave/balances/"
        response = self.client.post(url, {"year": self.balance.year}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["created"], 0)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.used_days, 5)
        self.leave_policy.accrual_enabled = True
        self.leave_policy.accrual_frequency = "MONTHLY"
        self.leave_policy.save()
        response = self.client.post(url, {"year": self.balance.year + 1}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        created = LeaveBalance.objects.get(employee=self.employee, leave_type=self.leave_type, year=self.balance.year + 1)
        self.assertTrue(created.accrual_enabled)
        self.assertEqual(created.accrual_frequency, "MONTHLY")

    def test_employee_cannot_initialize_balances(self):
        self.client.force_authenticate(self.employee_user)
        response = self.client.post(f"/api/leave/organizations/{self.organization.id}/leave/balances/", {"year": 2027}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_invalid_year_is_rejected(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(f"/api/leave/organizations/{self.organization.id}/leave/balances/", {"year": "invalid"}, format="json")
        self.assertEqual(response.status_code, 400)
