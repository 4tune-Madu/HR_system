from django.contrib import admin

from .models import (
    Employee,
    EmployeeIdentity,
    EmployeeContact,
    EmployeeAssignment,
    Employment,
    NextOfKin,
    EmergencyContact,
    EmployeeDocument,
)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_number",
        "organization",
        "user",
        "is_active",
        "created_at",
    )

    search_fields = (
        "employee_number",
        "organization__name",
        "user__email",
    )

    list_filter = (
        "is_active",
        "organization",
    )


@admin.register(EmployeeIdentity)
class EmployeeIdentityAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "first_name",
        "last_name",
        "date_of_birth",
        "gender",
    )

    search_fields = (
        "employee__employee_number",
        "first_name",
        "last_name",
    )


@admin.register(EmployeeContact)
class EmployeeContactAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "company_email",
        "personal_email",
        "phone_number",
    )

    search_fields = (
        "employee__employee_number",
        "company_email",
        "personal_email",
        "phone_number",
    )


@admin.register(EmployeeAssignment)
class EmployeeAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "branch",
        "department",
        "team",
        "position",
        "job_grade",
        "manager",
    )

    list_filter = (
        "branch",
        "department",
        "job_grade",
    )

    search_fields = (
        "employee__employee_number",
        "department__name",
        "position__title",
    )


@admin.register(Employment)
class EmploymentAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "employment_type",
        "employment_status",
        "confirmation_status",
        "employment_start_date",
        "confirmation_date",
    )

    list_filter = (
        "employment_type",
        "employment_status",
        "confirmation_status",
    )

    search_fields = (
        "employee__employee_number",
    )


@admin.register(NextOfKin)
class NextOfKinAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "full_name",
        "relationship",
        "phone_number",
        "is_primary",
    )

    list_filter = (
        "is_primary",
    )

    search_fields = (
        "employee__employee_number",
        "full_name",
        "relationship",
        "phone_number",
    )


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "full_name",
        "relationship",
        "phone_number",
        "is_primary",
    )

    list_filter = (
        "is_primary",
    )

    search_fields = (
        "employee__employee_number",
        "full_name",
        "phone_number",
    )


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "name",
        "document_type",
        "issue_date",
        "expiry_date",
        "created_at",
    )

    list_filter = (
        "document_type",
    )

    search_fields = (
        "employee__employee_number",
        "name",
    )