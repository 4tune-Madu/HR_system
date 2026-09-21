from django.test import TestCase

from rest_framework.test import APIRequestFactory

from apps.access.models import (
    Permission,
    Role,
    OrganizationMembership,
)
from apps.access.permissions import (
    CanViewEmployees,
    CanCreateEmployees,
)
from apps.access.services import RoleService

from apps.accounts.models import User
from apps.organization.models import Organization


class AccessPermissionTests(TestCase):

    def setUp(self):

        self.factory = APIRequestFactory()

        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
        )

        self.other_organization = Organization.objects.create(
            name="Other Company",
            legal_name="Other Company Limited",
        )

        self.view_permission = Permission.objects.create(
            code="employee.view",
            name="View Employees",
            description="Allows viewing employees.",
        )

        self.create_permission = Permission.objects.create(
            code="employee.create",
            name="Create Employees",
            description="Allows creating employees.",
        )

        self.role = Role.objects.create(
            organization=self.organization,
            name="HR Manager",
            code="HR_MANAGER",
        )

        self.role.permissions.add(
            self.view_permission,
            self.create_permission,
        )

        self.user = User.objects.create_user(
            email="hr@testcompany.com",
            password="TestPassword123!",
            first_name="John",
            last_name="Doe",
        )

        self.membership = OrganizationMembership.objects.create(
            user=self.user,
            organization=self.organization,
            role=self.role,
            is_active=True,
        )

    def make_request(self, user):

        request = self.factory.get(
            f"/api/organizations/{self.organization.id}/employees/"
        )

        request.user = user

        return request

    def make_view(self):

        class TestView:
            kwargs = {
                "organization_id": str(
                    self.organization.id
                )
            }

        return TestView()

    def test_authenticated_user_with_permission_is_allowed(self):

        request = self.make_request(self.user)
        view = self.make_view()

        permission = CanViewEmployees()

        result = permission.has_permission(
            request,
            view,
        )

        self.assertTrue(result)

        self.assertEqual(
            request.organization,
            self.organization,
        )

    def test_authenticated_user_without_permission_is_denied(self):

        role_without_create = Role.objects.create(
            organization=self.organization,
            name="Viewer",
            code="VIEWER",
        )

        viewer = User.objects.create_user(
            email="viewer@testcompany.com",
            password="TestPassword123!",
            first_name="Viewer",
            last_name="User",
        )

        OrganizationMembership.objects.create(
            user=viewer,
            organization=self.organization,
            role=role_without_create,
            is_active=True,
        )

        request = self.make_request(viewer)
        view = self.make_view()

        permission = CanCreateEmployees()

        result = permission.has_permission(
            request,
            view,
        )

        self.assertFalse(result)

    def test_user_without_membership_is_denied(self):

        user = User.objects.create_user(
            email="nomembership@testcompany.com",
            password="TestPassword123!",
            first_name="No",
            last_name="Membership",
        )

        request = self.make_request(user)
        view = self.make_view()

        permission = CanViewEmployees()

        result = permission.has_permission(
            request,
            view,
        )

        self.assertFalse(result)

    def test_user_from_another_organization_is_denied(self):

        request = self.factory.get(
            f"/api/organizations/"
            f"{self.other_organization.id}/employees/"
        )

        request.user = self.user

        class TestView:
            kwargs = {
                "organization_id": str(
                    self.other_organization.id
                )
            }

        permission = CanViewEmployees()

        result = permission.has_permission(
            request,
            TestView(),
        )

        self.assertFalse(result)

    def test_inactive_membership_is_denied(self):

        self.membership.is_active = False
        self.membership.save()

        request = self.make_request(self.user)
        view = self.make_view()

        permission = CanViewEmployees()

        result = permission.has_permission(
            request,
            view,
        )

        self.assertFalse(result)

    def test_unauthenticated_user_is_denied(self):

        request = self.factory.get(
            f"/api/organizations/{self.organization.id}/employees/"
        )

        request.user = User()

        view = self.make_view()

        permission = CanViewEmployees()

        result = permission.has_permission(
            request,
            view,
        )

        self.assertFalse(result)