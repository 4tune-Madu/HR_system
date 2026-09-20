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

class CanProvisionEmployeeAccounts(
    HasOrganizationPermission
):
    required_permission = (
        "employee.account.provision"
    )


class CanInviteEmployeeAccounts(
    HasOrganizationPermission
):
    required_permission = (
        "employee.account.invite"
    )

class CanActivateEmployees(
    HasOrganizationPermission
):
    required_permission = "employee.activate"

class CanViewLeave(
    HasOrganizationPermission
):
    required_permission = "leave.view"


class CanRequestLeave(
    HasOrganizationPermission
):
    required_permission = "leave.request"


class CanApproveLeave(
    HasOrganizationPermission
):
    required_permission = "leave.approve"

class CanManageLeave(
    HasOrganizationPermission
):
    required_permission = "leave.manage"