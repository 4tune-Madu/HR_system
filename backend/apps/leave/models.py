import uuid
from django.db.models import Sum
from django.db.models import Q
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from apps.organization.models import Organization
from apps.employee.models import Employee
from django.conf import settings
from django.core.exceptions import ValidationError

class LeaveType(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="leave_types",
    )

    code = models.CharField(
        max_length=50,
    )

    name = models.CharField(
        max_length=100,
    )

    description = models.TextField(
        blank=True,
    )

    is_paid = models.BooleanField(
        default=True,
    )

    requires_approval = models.BooleanField(
        default=True,
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
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "code",
                ],
                name="unique_leave_type_code_per_organization",
            ),
        ]

    def __str__(self):
        return self.name


class LeavePolicy(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="leave_policies",
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="policies",
    )

    days_per_year = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    minimum_days_per_request = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
    )

    maximum_days_per_request = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    allow_half_day = models.BooleanField(
        default=False,
    )

    allow_carry_forward = models.BooleanField(
        default=False,
    )

    maximum_carry_forward_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    prorate_for_new_hires = models.BooleanField(
        default=False,
    )

    accrual_enabled = models.BooleanField(
        default=False,
    )

    accrual_frequency = models.CharField(
        max_length=20,
        choices=[
            ("MONTHLY", "Monthly"),
            ("ANNUAL", "Annual"),
        ],
        default="ANNUAL",
    )

    accrual_start_month = models.PositiveSmallIntegerField(
        default=1,
    )

    requires_attachment = models.BooleanField(
        default=False,
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
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "leave_type",
                ],
                name="unique_leave_policy_per_type_and_organization",
            ),

            models.CheckConstraint(
                condition=Q(days_per_year__gte=0),
                name="leave_policy_days_per_year_non_negative",
            ),

            models.CheckConstraint(
                condition=Q(
                    minimum_days_per_request__gte=0
                ),
                name="leave_policy_minimum_days_non_negative",
            ),

            models.CheckConstraint(
                condition=(
                    Q(maximum_days_per_request__isnull=True)
                    | Q(maximum_days_per_request__gte=0)
                ),
                name="leave_policy_maximum_days_non_negative",
            ),

            models.CheckConstraint(
                condition=(
                    Q(maximum_carry_forward_days__isnull=True)
                    | Q(maximum_carry_forward_days__gte=0)
                ),
                name="leave_policy_max_carry_non_negative",
            ),
        ]

    def __str__(self):
        return (
            f"{self.organization} - "
            f"{self.leave_type}"
        )


class LeaveBalance(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_balances",
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="employee_balances",
    )

    year = models.PositiveIntegerField()

    entitlement_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )

    carry_forward_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0),
        ],
    )

    used_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0),
        ],
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    accrual_enabled = models.BooleanField(
        default=False,
    )

    accrual_frequency = models.CharField(
        max_length=20,
        choices=[
            ("MONTHLY", "Monthly"),
            ("ANNUAL", "Annual"),
        ],
        default="ANNUAL",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "employee",
                    "leave_type",
                    "year",
                ],
                name="unique_employee_leave_balance_per_year",
            ),
        ]


    @property
    def credit_adjustments(self):
        return (
            self.adjustments
            .filter(
                adjustment_type=(
                    LeaveBalanceAdjustment
                    .AdjustmentType.CREDIT
                )
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )
    
    
    @property
    def debit_adjustments(self):
        return (
            self.adjustments
            .filter(
                adjustment_type=(
                    LeaveBalanceAdjustment
                    .AdjustmentType.DEBIT
                )
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )
    
    
    @property
    def accrued_days(self):
        return (
            self.accruals
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )
    
    
    @property
    def available_entitlement_days(self):
        if not self.accrual_enabled:
            return self.entitlement_days
    
        return self.accrued_days
    
    
    @property
    def total_available_days(self):
        return (
            self.available_entitlement_days
            + self.carry_forward_days
            + self.credit_adjustments
            - self.debit_adjustments
        )
    
    
    @property
    def remaining_days(self):
        return max(
            self.total_available_days
            - self.used_days,
            Decimal("0"),
        )
        
    def __str__(self):
        return (
            f"{self.employee} - "
            f"{self.leave_type} - "
            f"{self.year}"
        )

class LeaveBalanceAdjustment(models.Model):

    class AdjustmentType(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        DEBIT = "DEBIT", "Debit"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    balance = models.ForeignKey(
        LeaveBalance,
        on_delete=models.PROTECT,
        related_name="adjustments",
    )

    amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    adjustment_type = models.CharField(
        max_length=10,
        choices=AdjustmentType.choices,
    )

    reason = models.TextField()

    adjusted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="leave_balance_adjustments",
    )

    adjusted_at = models.DateTimeField(
        auto_now_add=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-adjusted_at",
        ]

    def __str__(self):
        return (
            f"{self.adjustment_type} "
            f"{self.amount} - "
            f"{self.balance}"
        )


class LeaveRequest(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="leave_requests",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="leave_requests",
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="requests",
    )

    start_date = models.DateField()

    end_date = models.DateField()

    requested_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    reason = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_leave_requests",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    review_comment = models.TextField(
        blank=True,
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return (
            f"{self.employee} - "
            f"{self.leave_type} - "
            f"{self.start_date}"
        )

    def clean(self):

        if self.end_date < self.start_date:
            raise ValidationError(
                {
                    "end_date": (
                        "End date cannot be before "
                        "start date."
                    )
                }
            )

        if self.requested_days <= 0:
            raise ValidationError(
                {
                    "requested_days": (
                        "Requested days must be greater than zero."
                    )
                }
            )


class WorkSchedule(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="work_schedules",
    )

    code = models.CharField(
        max_length=50,
    )

    name = models.CharField(
        max_length=100,
    )

    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)

    is_default = models.BooleanField(
        default=False,
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
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "code",
                ],
                name="unique_work_schedule_code_per_organization",
            ),
        ]

    def __str__(self):
        return self.name

class PublicHoliday(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="public_holidays",
    )

    date = models.DateField()

    name = models.CharField(
        max_length=150,
    )

    description = models.TextField(
        blank=True,
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
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "date",
                ],
                name="unique_public_holiday_per_organization",
            ),
        ]

    def __str__(self):
        return (
            f"{self.name} - {self.date}"
        )

class EmployeeWorkSchedule(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="work_schedule_assignments",
    )

    work_schedule = models.ForeignKey(
        WorkSchedule,
        on_delete=models.PROTECT,
        related_name="employee_assignments",
    )

    effective_from = models.DateField()

    effective_to = models.DateField(
        null=True,
        blank=True,
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
        ordering = [
            "-effective_from",
        ]

    def __str__(self):
        return (
            f"{self.employee} - "
            f"{self.work_schedule} - "
            f"{self.effective_from}"
        )

    def clean(self):

        if (
            self.effective_to is not None
            and self.effective_to
            < self.effective_from
        ):
            raise ValidationError(
                {
                    "effective_to": (
                        "Effective end date cannot be "
                        "before the effective start date."
                    )
                }
            )
    
        if (
            self.work_schedule.organization_id
            != self.employee.organization_id
        ):
            raise ValidationError(
                {
                    "work_schedule": (
                        "Work schedule must belong "
                        "to the employee's organization."
                    )
                }
            )


class LeaveEntitlement(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_entitlements",
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="employee_entitlements",
    )

    year = models.PositiveIntegerField()

    days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    is_override = models.BooleanField(
        default=False,
    )

    reason = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "employee",
                    "leave_type",
                    "year",
                ],
                name="unique_employee_leave_entitlement",
            ),
        ]

    def __str__(self):
        return (
            f"{self.employee} - "
            f"{self.leave_type} - "
            f"{self.year}"
        )


class LeaveAccrual(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    balance = models.ForeignKey(
        LeaveBalance,
        on_delete=models.PROTECT,
        related_name="accruals",
    )

    year = models.PositiveIntegerField()

    period_month = models.PositiveSmallIntegerField()

    amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    accrued_at = models.DateTimeField(
        auto_now_add=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "balance",
                    "year",
                    "period_month",
                ],
                name="unique_leave_accrual_period",
            ),
        ]

        ordering = [
            "-year",
            "-period_month",
        ]

    @property
    def accrued_days(self):
        return (
            self.accruals
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )

class LeaveApprovalRule(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="leave_approval_rules",
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="approval_rules",
    )

    approval_level = models.PositiveIntegerField()

    minimum_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
    )

    maximum_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
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
        ordering = [
            "approval_level",
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(
                    approval_level__gte=1
                ),
                name="leave_approval_rule_level_positive",
            ),

            models.CheckConstraint(
                condition=Q(
                    minimum_days__gte=0
                ),
                name="leave_approval_rule_min_days_non_negative",
            ),

            models.CheckConstraint(
                condition=(
                    Q(maximum_days__isnull=True)
                    | Q(maximum_days__gte=0)
                ),
                name="leave_approval_rule_max_days_non_negative",
            ),

            models.UniqueConstraint(
                fields=[
                    "organization",
                    "leave_type",
                    "approval_level",
                ],
                condition=Q(
                    leave_type__isnull=False
                ),
                name=(
                    "unique_leave_approval_rule_specific_level"
                ),
            ),

            models.UniqueConstraint(
                fields=[
                    "organization",
                    "approval_level",
                ],
                condition=Q(
                    leave_type__isnull=True
                ),
                name=(
                    "unique_leave_approval_rule_default_level"
                ),
            ),
        ]

    def clean(self):
        if (
            self.maximum_days is not None
            and self.minimum_days > self.maximum_days
        ):
            raise ValidationError(
                {
                    "maximum_days": (
                        "Maximum days cannot be less "
                        "than minimum days."
                    )
                }
            )

        if (
            self.leave_type is not None
            and self.leave_type.organization_id
            != self.organization_id
        ):
            raise ValidationError(
                {
                    "leave_type": (
                        "Leave type must belong "
                        "to the same organization."
                    )
                }
            )

    def applies_to_days(
        self,
        requested_days,
    ):
        requested_days = Decimal(
            requested_days
        )

        if requested_days < self.minimum_days:
            return False

        if (
            self.maximum_days is not None
            and requested_days > self.maximum_days
        ):
            return False

        return True

    def __str__(self):
        scope = (
            self.leave_type.name
            if self.leave_type
            else "All Leave Types"
        )

        return (
            f"{scope} - "
            f"Level {self.approval_level}"
        )


class LeaveApprovalStep(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SKIPPED = "SKIPPED", "Skipped"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    leave_request = models.ForeignKey(
        LeaveRequest,
        on_delete=models.CASCADE,
        related_name="approval_steps",
    )

    approval_level = models.PositiveIntegerField()

    approver_employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="leave_approval_steps",
    )

    approver_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="leave_approval_steps",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    comment = models.TextField(
        blank=True,
    )

    acted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "approval_level",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "leave_request",
                    "approval_level",
                ],
                name=(
                    "unique_leave_approval_step_per_level"
                ),
            ),
        ]

    def __str__(self):
        return (
            f"{self.leave_request} - "
            f"Level {self.approval_level} - "
            f"{self.status}"
        )