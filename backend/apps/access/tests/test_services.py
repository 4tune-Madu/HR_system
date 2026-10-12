from django.test import TestCase

from apps.access.models import (
    Permission,
    Role,
    OrganizationMembership,
)
from apps.access.services import AccessService
from apps.accounts.models import User
from apps.organization.models import Organization


class AccessServiceTests(TestCase):

    def setUp(self):

        # Organizations

        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
        )

        self.other_organization = Organization.objects.create(
            name="Other Company",
            legal_name="Other Company Limited",
        )

        # Permissions

        self.employee_view = Permission.objects.create(
            code="employee.view",
            name="View Employees",
            description="Allows viewing employees.",
        )

        self.employee_create = Permission.objects.create(
            code="employee.create",
            name="Create Employees",
            description="Allows creating employees.",
        )

        # Role

        self.hr_manager_role = Role.objects.create(
            organization=self.organization,
            name="HR Manager",
            code="HR_MANAGER",
            description="HR Manager role.",
        )

        self.hr_manager_role.permissions.add(
            self.employee_view,
            self.employee_create,
        )

        # User

        self.user = User.objects.create_user(
            email="hr@testcompany.com",
            password="TestPassword123!",
            first_name="John",
            last_name="Doe",
        )

        # Membership

        self.membership = (
            OrganizationMembership.objects.create(
                user=self.user,
                organization=self.organization,
                role=self.hr_manager_role,
            )
        )

    def test_get_membership_returns_active_membership(self):

        membership = AccessService.get_membership(
            user=self.user,
            organization=self.organization,
        )

        self.assertEqual(
            membership,
            self.membership,
        )

    def test_get_membership_returns_none_for_other_organization(self):

        membership = AccessService.get_membership(
            user=self.user,
            organization=self.other_organization,
        )

        self.assertIsNone(membership)

    def test_has_permission_returns_true_when_user_has_permission(self):

        result = AccessService.has_permission(
            user=self.user,
            organization=self.organization,
            permission="employee.create",
        )

        self.assertTrue(result)

    def test_has_permission_returns_false_when_permission_is_missing(self):

        result = AccessService.has_permission(
            user=self.user,
            organization=self.organization,
            permission="payroll.process",
        )

        self.assertFalse(result)

    def test_user_without_membership_is_denied(self):

        user = User.objects.create_user(
            email="nomembership@testcompany.com",
            password="TestPassword123!",
            first_name="Jane",
            last_name="Doe",
        )

        result = AccessService.has_permission(
            user=user,
            organization=self.organization,
            permission="employee.create",
        )

        self.assertFalse(result)

    def test_user_cannot_access_another_organization(self):

        result = AccessService.has_permission(
            user=self.user,
            organization=self.other_organization,
            permission="employee.create",
        )

        self.assertFalse(result)

    def test_inactive_membership_is_denied(self):

        self.membership.is_active = False
        self.membership.save()

        result = AccessService.has_permission(
            user=self.user,
            organization=self.organization,
            permission="employee.create",
        )

        self.assertFalse(result)

    def test_get_role_returns_users_role(self):

        role = AccessService.get_role(
            user=self.user,
            organization=self.organization,
        )

        self.assertEqual(
            role,
            self.hr_manager_role,
        )

    def test_get_role_returns_none_without_membership(self):

        user = User.objects.create_user(
            email="norole@testcompany.com",
            password="TestPassword123!",
            first_name="No",
            last_name="Role",
        )

        role = AccessService.get_role(
            user=user,
            organization=self.organization,
        )

        self.assertIsNone(role)


    def test_assign_role_creates_membership(self):

        membership = AccessService.assign_role(
            user=self.user,
            organization=self.organization,
            role=self.hr_manager_role,
        )

        self.assertEqual(
            membership.user,
            self.user,
        )

        self.assertEqual(
            membership.organization,
            self.organization,
        )

        self.assertEqual(
            membership.role,
            self.hr_manager_role,
        )

        self.assertTrue(
            membership.is_active
        )


    def test_assign_role_updates_existing_membership(self):
    
        first_membership = self.membership
    
        manager_role = Role.objects.create(
            organization=self.organization,
            name="Manager",
            code="MANAGER",
        )
    
        second_membership = AccessService.assign_role(
            user=self.user,
            organization=self.organization,
            role=manager_role,
        )
    
        self.assertEqual(
            first_membership.id,
            second_membership.id,
        )
    
        self.assertEqual(
            second_membership.role,
            manager_role,
        )
        
    def test_assign_role_rejects_role_from_another_organization(self):

        other_role = Role.objects.create(
            organization=self.other_organization,
            name="Other HR Manager",
            code="OTHER_HR_MANAGER",
        )

        with self.assertRaises(ValueError):

            AccessService.assign_role(
                user=self.user,
                organization=self.organization,
                role=other_role,
            )