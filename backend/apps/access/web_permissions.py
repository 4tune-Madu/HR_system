from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

from .services import AccessService
from apps.organization.models import Organization


class OrganizationPermissionRequiredMixin(
    AccessMixin
):
    required_permission = None

    def dispatch(
        self,
        request,
        *args,
        **kwargs,
    ):

        if not request.user.is_authenticated:
            return self.handle_no_permission()

        organization_id = kwargs.get(
            "organization_id"
        )

        if not organization_id:
            raise PermissionDenied

        membership = (
            AccessService
            .get_membership_by_organization_id(
                user=request.user,
                organization_id=organization_id,
            )
        )

        if not membership:
            if not request.user.is_superuser:
                raise PermissionDenied

            organization = Organization.objects.filter(
                id=organization_id,
                is_active=True,
            ).first()
            if not organization:
                raise PermissionDenied

            request.organization = organization
            request.organization_membership = None
            return super().dispatch(
                request,
                *args,
                **kwargs,
            )

        if not self.required_permission:
            raise PermissionDenied

        allowed = AccessService.has_permission(
            user=request.user,
            organization=membership.organization,
            permission=self.required_permission,
        )

        if not allowed:
            raise PermissionDenied

        request.organization = (
            membership.organization
        )

        request.organization_membership = (
            membership
        )

        return super().dispatch(
            request,
            *args,
            **kwargs,
        )
