from django.contrib import admin

from .models import (
    Permission,
    Role,
    OrganizationMembership,
)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):

    list_display = [
        "code",
        "name",
        "created_at",
    ]

    search_fields = [
        "code",
        "name",
    ]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):

    list_display = [
        "name",
        "code",
        "organization",
        "is_system_role",
    ]

    list_filter = [
        "organization",
        "is_system_role",
    ]

    search_fields = [
        "name",
        "code",
    ]

    filter_horizontal = [
        "permissions",
    ]


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):

    list_display = [
        "user",
        "organization",
        "role",
        "is_active",
    ]

    list_filter = [
        "organization",
        "role",
        "is_active",
    ]

    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
    ]