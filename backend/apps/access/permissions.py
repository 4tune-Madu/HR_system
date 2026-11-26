from rest_framework.permissions import BasePermission

from apps.access.services import AccessService
from apps.organization.models import Organization


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
            if not request.user.is_superuser:
                return False

            organization = Organization.objects.filter(
                id=organization_id,
                is_active=True,
            ).first()
            if not organization:
                return False

            request.organization = organization
            request.organization_membership = None
            return True

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

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            return True
        if request.method != "GET" or not view.kwargs.get("employee_id") or not getattr(request, "organization", None):
            return False

        from apps.employee.models import Employee

        is_own_record = Employee.objects.filter(
            id=view.kwargs["employee_id"],
            organization=request.organization,
            user=request.user,
            is_active=True,
        ).exists()
        return is_own_record and AccessService.has_permission(
            user=request.user,
            organization=request.organization,
            permission="employee.view_own",
        )


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

class CanViewAttendanceDevices(
    HasOrganizationPermission
):
    required_permission = "attendance.device.view"


class CanManageAttendanceDevices(
    HasOrganizationPermission
):
    required_permission = "attendance.device.manage"


class CanManageAttendanceSettings(
    HasOrganizationPermission
):
    required_permission = (
        "attendance.settings.manage"
    )

class CanViewAttendanceRecords(
    HasOrganizationPermission
):
    required_permission = "attendance.view"

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            return True
        if request.method != "GET" or not getattr(request, "organization", None):
            return False
        from apps.employee.models import Employee
        is_employee = Employee.objects.filter(
            organization=request.organization,
            user=request.user,
            is_active=True,
        ).exists()
        return is_employee and AccessService.has_permission(
            user=request.user,
            organization=request.organization,
            permission="employee.view_own",
        )

class CanManageManualAttendance(
    HasOrganizationPermission
):
    required_permission = (
        "attendance.manual.manage"
    )

class CanManageAttendanceReconciliation(
    HasOrganizationPermission
):
    required_permission = (
        "attendance.reconciliation.manage"
    )


class CanViewOrganization(HasOrganizationPermission):
    required_permission = "organization.view"


class CanManageOrganizationStructure(
    HasOrganizationPermission
):
    required_permission = "organization.structure.manage"
