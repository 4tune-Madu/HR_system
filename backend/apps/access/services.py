from django.db import transaction

from apps.access.models import (
    Permission,
    Role,
    OrganizationMembership,
)
from apps.access.roles import ROLE_PERMISSIONS

class AccessService:

    @staticmethod
    def get_membership(
        *,
        user,
        organization,
    ):
        """
        Return the user's active membership
        in the organization.
        """

        return (
            OrganizationMembership.objects
            .select_related("role", "organization")
            .prefetch_related("role__permissions")
            .filter(
                user=user,
                organization=organization,
                is_active=True,
            )
            .first()
        )

    @staticmethod
    def has_permission(
        *,
        user,
        organization,
        permission,
    ):
        """
        Check whether a user has a specific
        permission within an organization.
        """

        membership = AccessService.get_membership(
            user=user,
            organization=organization,
        )

        if not membership:
            return False

        return membership.role.permissions.filter(
            code=permission,
        ).exists()

    @staticmethod
    def get_role(
        *,
        user,
        organization,
    ):
        """
        Return the user's active role
        within the organization.
        """

        membership = AccessService.get_membership(
            user=user,
            organization=organization,
        )

        if not membership:
            return None

        return membership.role


    @staticmethod
    @transaction.atomic
    def assign_role(
        *,
        user,
        organization,
        role,
    ):
        """
        Assign a role to a user within an organization.
        """

        if role.organization_id != organization.id:
            raise ValueError(
                "Role does not belong to this organization."
            )

        membership, created = (
            OrganizationMembership.objects.update_or_create(
                user=user,
                organization=organization,
                defaults={
                    "role": role,
                    "is_active": True,
                },
            )
        )

        return membership

    @staticmethod
    def get_membership_by_organization_id(
        *,
        user,
        organization_id,
    ):
        return (
            OrganizationMembership.objects
            .select_related(
                "role",
                "organization",
            )
            .prefetch_related(
                "role__permissions",
            )
            .filter(
                user=user,
                organization_id=organization_id,
                is_active=True,
            )
            .first()
        )

class RoleService:

    @staticmethod
    @transaction.atomic
    def provision_system_role(
        *,
        organization,
        role_code,
    ):
        """
        Create an organization-specific role
        from a system role definition.
        """

        if role_code not in ROLE_PERMISSIONS:
            raise ValueError(
                f"Unknown system role: {role_code}"
            )

        # -----------------------------------------
        # Ensure system permissions exist
        # -----------------------------------------

        PermissionService.provision_system_permissions()

        # -----------------------------------------
        # Get role permissions
        # -----------------------------------------

        role_permissions = ROLE_PERMISSIONS[
            role_code
        ]

        # -----------------------------------------
        # Create organization role
        # -----------------------------------------

        role, created = Role.objects.get_or_create(
            organization=organization,
            code=role_code,
            defaults={
                "name": role_code.replace(
                    "_",
                    " ",
                ).title(),

                "is_system_role": True,
            },
        )

        # -----------------------------------------
        # Attach permissions
        # -----------------------------------------

        permissions = Permission.objects.filter(
            code__in=role_permissions,
        )

        role.permissions.set(
            permissions
        )

        return role
    

class PermissionService:

    @staticmethod
    @transaction.atomic
    def provision_system_permissions():
        """
        Ensure all permissions defined in ROLE_PERMISSIONS
        exist in the database.
        """

        permission_codes = set()

        for permissions in ROLE_PERMISSIONS.values():
            permission_codes.update(permissions)

        for code in permission_codes:

            Permission.objects.get_or_create(
                code=code,
                defaults={
                    "name": code.replace(
                        ".",
                        " ",
                    ).replace(
                        "_",
                        " ",
                    ).title(),
                },
            )