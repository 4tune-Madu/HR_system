import uuid

from django.conf import settings
from django.db import models

from apps.organization.models import (
    Branch,
    Department,
    JobGrade,
    Organization,
    Position,
    Team,
)


class Employee(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="employees",
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_profile",
    )

    employee_number = models.CharField(
        max_length=50,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["employee_number"]

        constraints = [
            models.UniqueConstraint(
                fields=["organization", "employee_number"],
                name="unique_employee_number_per_organization",
            ),
        ]

    def __str__(self):
        return self.employee_number


class EmployeeIdentity(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="identity",
    )

    first_name = models.CharField(
        max_length=100,
    )

    middle_name = models.CharField(
        max_length=100,
        blank=True,
    )

    last_name = models.CharField(
        max_length=100,
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    gender = models.CharField(
        max_length=30,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    @property
    def full_name(self):
        return " ".join(
            part
            for part in [
                self.first_name,
                self.middle_name,
                self.last_name,
            ]
            if part
        )

    def __str__(self):
        return self.full_name

class EmployeeContact(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="contact",
    )

    personal_email = models.EmailField(
        blank=True,
    )

    company_email = models.EmailField(
        blank=True,
    )

    phone_number = models.CharField(
        max_length=30,
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.company_email or self.personal_email or str(
            self.employee
        )

class EmployeeAssignment(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="assignment",
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employee_assignments",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employee_assignments",
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employee_assignments",
    )

    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employee_assignments",
    )

    job_grade = models.ForeignKey(
        JobGrade,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employee_assignments",
    )

    manager = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direct_reports",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return str(self.employee)

class Employment(models.Model):

    class EmploymentType(models.TextChoices):
        PERMANENT = "PERMANENT", "Permanent"
        CONTRACT = "CONTRACT", "Contract"
        TEMPORARY = "TEMPORARY", "Temporary"
        INTERN = "INTERN", "Intern"
        PART_TIME = "PART_TIME", "Part Time"

    class EmploymentStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        PROBATION = "PROBATION", "Probation"
        SUSPENDED = "SUSPENDED", "Suspended"
        RESIGNED = "RESIGNED", "Resigned"
        TERMINATED = "TERMINATED", "Terminated"
        RETIRED = "RETIRED", "Retired"

    class ConfirmationStatus(models.TextChoices):
        NOT_APPLICABLE = "NOT_APPLICABLE", "Not Applicable"
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        EXTENDED = "EXTENDED", "Extended"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="employment",
    )

    employment_type = models.CharField(
        max_length=30,
        choices=EmploymentType.choices,
        default=EmploymentType.PERMANENT,
    )

    employment_status = models.CharField(
        max_length=30,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.PROBATION,
    )

    offer_date = models.DateField(
        null=True,
        blank=True,
    )

    employment_start_date = models.DateField(
        null=True,
        blank=True,
    )

    probation_end_date = models.DateField(
        null=True,
        blank=True,
    )

    confirmation_status = models.CharField(
        max_length=30,
        choices=ConfirmationStatus.choices,
        default=ConfirmationStatus.PENDING,
    )

    confirmation_date = models.DateField(
        null=True,
        blank=True,
    )

    date_left = models.DateField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.employee} Employment"

class NextOfKin(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="next_of_kin",
    )

    full_name = models.CharField(
        max_length=200,
    )

    relationship = models.CharField(
        max_length=100,
    )

    phone_number = models.CharField(
        max_length=30,
    )

    email = models.EmailField(
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    is_primary = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.full_name} - {self.relationship}"

class EmergencyContact(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="emergency_contacts",
    )

    full_name = models.CharField(
        max_length=200,
    )

    relationship = models.CharField(
        max_length=100,
        blank=True,
    )

    phone_number = models.CharField(
        max_length=30,
    )

    alternative_phone_number = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    is_primary = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.full_name} - {self.employee}"

class EmployeeDocument(models.Model):

    class DocumentType(models.TextChoices):
        EMPLOYMENT_LETTER = "EMPLOYMENT_LETTER", "Employment Letter"
        OFFER_LETTER = "OFFER_LETTER", "Offer Letter"
        CONTRACT = "CONTRACT", "Contract"
        IDENTIFICATION = "IDENTIFICATION", "Identification"
        CERTIFICATE = "CERTIFICATE", "Certificate"
        RESUME = "RESUME", "Resume"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
    )

    name = models.CharField(
        max_length=255,
    )

    file = models.FileField(
        upload_to="employee_documents/%Y/%m/",
    )

    description = models.TextField(
        blank=True,
    )

    issue_date = models.DateField(
        null=True,
        blank=True,
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
    )

    is_archived = models.BooleanField(
        default=False,
    )

    archived_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="archived_employee_documents",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.employee} - {self.name}"