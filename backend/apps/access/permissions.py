from rest_framework.permissions import BasePermission

from apps.access.services import AccessService


class HasOrganizationPermission(BasePermission):

    required_permission = None

    def has_permission(
        self,
        request,
        view,
    ):

        if not request.user.is_authenticated:
            return False

        organization_id = view.kwargs.get(
            "organization_id"
        )

        if not organization_id:
            return False

        membership = (
            AccessService
            .get_membership_by_organization_id(
                user=request.user,
                organization_id=organization_id,
            )
        )

        if not membership:
            return False

        request.organization = (
            membership.organization
        )

        request.organization_membership = (
            membership
        )

        if not self.required_permission:
            return False

        return AccessService.has_permission(
            user=request.user,
            organization=membership.organization,
            permission=self.required_permission,
        )


class CanViewEmployees(
    HasOrganizationPermission
):

    required_permission = "employee.view"


class CanCreateEmployees(
    HasOrganizationPermission
):

    required_permission = "employee.create"


class CanUpdateEmployees(
    HasOrganizationPermission
):

    required_permission = "employee.update"


class CanDeactivateEmployees(
    HasOrganizationPermission
):

    required_permission = "employee.deactivate"

class CanViewEmployeeDocuments(
    HasOrganizationPermission
):

    required_permission = (
        "employee.document.view"
    )


class CanUploadEmployeeDocuments(
    HasOrganizationPermission
):

    required_permission = (
        "employee.document.upload"
    )

class CanArchiveEmployeeDocuments(
    HasOrganizationPermission
):

    required_permission = (
        "employee.document.archive"
    )


class CanRestoreEmployeeDocuments(
    HasOrganizationPermission
):
    required_permission = (
        "employee.document.restore"
    )