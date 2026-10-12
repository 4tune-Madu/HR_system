from rest_framework.test import APITestCase


from rest_framework import status

from apps.accounts.models import User

from apps.access.services import (
    AccessService,
    RoleService,
)

from apps.organization.models import (
    Organization,
)


class OrganizationAttendanceSettingsAPITests(
    APITestCase
):

    def setUp(self):

        # -----------------------------------
        # Organization
        # -----------------------------------

        self.organization = (
            Organization.objects.create(
                name="Test Company",
                legal_name="Test Company Limited",
            )
        )

        # -----------------------------------
        # Organization Admin User
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

        self.role = (
            RoleService.provision_system_role(
                organization=self.organization,
                role_code="ORGANIZATION_ADMIN",
            )
        )

        # -----------------------------------
        # Organization Membership
        # -----------------------------------

        self.membership = (
            AccessService.assign_role(
                user=self.user,
                organization=self.organization,
                role=self.role,
            )
        )

        # -----------------------------------
        # Authenticate
        # -----------------------------------

        self.client.force_authenticate(
            user=self.user,
        )

    # =======================================
    # URL HELPER
    # =======================================

    def settings_url(self):
        return (
            f"/api/organization/"
            f"{self.organization.id}/"
            f"attendance/settings/"
        )

    # =======================================
    # GET SETTINGS
    # =======================================

    def test_get_attendance_settings(
        self,
    ):

        response = self.client.get(
            self.settings_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.data[
                "automatic_attendance_checkout_enabled"
            ]
        )

    # =======================================
    # PATCH SETTINGS - DISABLE
    # =======================================

    def test_disable_automatic_attendance_checkout(
        self,
    ):

        response = self.client.patch(
            self.settings_url(),
            {
                "automatic_attendance_checkout_enabled": (
                    False
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            response.data[
                "automatic_attendance_checkout_enabled"
            ]
        )

        self.organization.refresh_from_db()

        self.assertFalse(
            self.organization
            .automatic_attendance_checkout_enabled
        )

    # =======================================
    # PATCH SETTINGS - ENABLE
    # =======================================

    def test_enable_automatic_attendance_checkout(
        self,
    ):

        self.organization.automatic_attendance_checkout_enabled = (
            False
        )

        self.organization.save(
            update_fields=[
                "automatic_attendance_checkout_enabled",
            ]
        )

        response = self.client.patch(
            self.settings_url(),
            {
                "automatic_attendance_checkout_enabled": (
                    True
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.data[
                "automatic_attendance_checkout_enabled"
            ]
        )

        self.organization.refresh_from_db()

        self.assertTrue(
            self.organization
            .automatic_attendance_checkout_enabled
        )

    # =======================================
    # PATCH SETTINGS - PERSISTENCE
    # =======================================

    def test_attendance_setting_persists(
        self,
    ):

        self.client.patch(
            self.settings_url(),
            {
                "automatic_attendance_checkout_enabled": (
                    False
                ),
            },
            format="json",
        )

        self.organization.refresh_from_db()

        self.assertFalse(
            self.organization
            .automatic_attendance_checkout_enabled
        )

        response = self.client.get(
            self.settings_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            response.data[
                "automatic_attendance_checkout_enabled"
            ]
        )

    # =======================================
    # PERMISSION DENIED
    # =======================================

    def test_user_without_attendance_settings_permission_is_denied(
        self,
    ):

        manager_user = User.objects.create_user(
            email="manager@testcompany.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="Manager",
        )

        manager_role = (
            RoleService.provision_system_role(
                organization=self.organization,
                role_code="MANAGER",
            )
        )

        AccessService.assign_role(
            user=manager_user,
            organization=self.organization,
            role=manager_role,
        )

        self.client.force_authenticate(
            user=manager_user,
        )

        response = self.client.get(
            self.settings_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # =======================================
    # ORGANIZATION ISOLATION
    # =======================================

    def test_settings_cannot_be_accessed_by_user_from_another_organization(
        self,
    ):

        another_organization = (
            Organization.objects.create(
                name="Another Company",
                legal_name="Another Company Limited",
            )
        )

        another_user = User.objects.create_user(
            email="otheradmin@anothercompany.com",
            password="TestPassword123!",
            first_name="Other",
            last_name="Admin",
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

        self.client.force_authenticate(
            user=another_user,
        )

        response = self.client.get(
            self.settings_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )