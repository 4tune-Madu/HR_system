from rest_framework.test import APITestCase
from apps.employee.tests import test_api
from apps.employee.models import Employee


class EmployeeContactFieldsTests(APITestCase):
    setUp = test_api.EmployeeAPITests.setUp
    employee_list_url = test_api.EmployeeAPITests.employee_list_url
    employee_detail_url = test_api.EmployeeAPITests.employee_detail_url

    def test_create_and_update_contact_fields_and_next_of_kin(self):
        kin = {"full_name": "Sample Relative", "relationship": "Sibling", "phone_number": "08000000000", "is_primary": True}
        response = self.client.post(self.employee_list_url(), {
            "identity": {"first_name": "Sample", "last_name": "Employee"},
            "contact": {"other_phone_number": "08000000001", "cug_phone_number": "08000000002"},
            "next_of_kin": [kin],
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        employee_id = response.data["id"]
        self.assertEqual(response.data["contact"]["cug_phone_number"], "08000000002")
        self.assertEqual(response.data["next_of_kin"][0]["full_name"], "Sample Relative")
        url = self.employee_detail_url(employee_id)
        response = self.client.patch(url, {"contact": {"other_phone_number": "08000000003"}}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["next_of_kin"]), 1)
        response = self.client.patch(url, {"next_of_kin": [{**kin, "phone_number": "08000000004"}]}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["next_of_kin"][0]["phone_number"], "08000000004")
        self.assertEqual(self.client.patch(url, {"next_of_kin": []}, format="json").status_code, 200)
        self.assertFalse(Employee.objects.get(pk=employee_id).next_of_kin.exists())

    def test_incomplete_kin_is_rejected_on_partial_update(self):
        response = self.client.patch(self.employee_detail_url(self.employee.id), {"next_of_kin": [{"full_name": "Incomplete"}]}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_multiple_primary_contacts_roll_back_employee_creation(self):
        count = Employee.objects.count()
        kin = {"full_name": "Relative", "relationship": "Sibling", "phone_number": "08000000000", "is_primary": True}
        response = self.client.post(self.employee_list_url(), {"identity": {"first_name": "Sample", "last_name": "Employee"}, "next_of_kin": [kin, kin]}, format="json")
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(Employee.objects.count(), count)
