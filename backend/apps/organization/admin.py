from django.contrib import admin

from .models import (
    Branch,
    Department,
    JobGrade,
    Organization,
    Position,
    Team,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "legal_name",
        "email",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "legal_name",
        "registration_number",
    )

    list_filter = (
        "is_active",
    )


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "organization",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
        "organization__name",
    )

    list_filter = (
        "is_active",
        "organization",
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "organization",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
        "organization__name",
    )

    list_filter = (
        "is_active",
        "organization",
    )


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "department",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
        "department__name",
    )

    list_filter = (
        "is_active",
    )


@admin.register(JobGrade)
class JobGradeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "level",
        "organization",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
        "organization__name",
    )

    list_filter = (
        "is_active",
        "organization",
    )


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "code",
        "department",
        "job_grade",
        "organization",
        "is_active",
    )

    search_fields = (
        "title",
        "code",
        "department__name",
        "organization__name",
    )

    list_filter = (
        "is_active",
        "organization",
        "department",
        "job_grade",
    )