from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import (
    LeaveRequest,
    LeaveType,
    LeavePolicy,
    LeaveBalance,
    WorkSchedule,
    PublicHoliday,
    EmployeeWorkSchedule,
    LeaveEntitlement,
    LeaveBalanceAdjustment,
    LeaveAccrual,
    LeaveApprovalStep,
    LeaveApprovalRule,
)

from decimal import Decimal

class LeaveApprovalStepSerializer(
    serializers.ModelSerializer
):

    approver_employee_name = (
        serializers.SerializerMethodField()
    )

    approver_user_name = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = LeaveApprovalStep

        fields = [
            "id",
            "approval_level",
            "approver_employee",
            "approver_employee_name",
            "approver_user",
            "approver_user_name",
            "status",
            "comment",
            "acted_at",
            "created_at",
        ]

        read_only_fields = fields

    def get_approver_employee_name(
        self,
        obj,
    ):
        identity = getattr(
            obj.approver_employee,
            "identity",
            None,
        )

        if identity is None:
            return str(
                obj.approver_employee
            )

        return (
            f"{identity.first_name} "
            f"{identity.last_name}"
        ).strip()

    def get_approver_user_name(
        self,
        obj,
    ):
        return (
            f"{obj.approver_user.first_name} "
            f"{obj.approver_user.last_name}"
        ).strip()


class LeaveApprovalRuleSerializer(
    serializers.ModelSerializer
):

    leave_type_name = serializers.CharField(
        source="leave_type.name",
        read_only=True,
    )

    class Meta:
        model = LeaveApprovalRule

        fields = [
            "id",
            "organization",
            "leave_type",
            "leave_type_name",
            "approval_level",
            "minimum_days",
            "maximum_days",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "organization",
            "leave_type_name",
            "created_at",
            "updated_at",
        ]


class LeaveApprovalRuleWriteSerializer(
    serializers.Serializer
):

    leave_type = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

    approval_level = serializers.IntegerField(
        min_value=1,
    )

    minimum_days = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=Decimal("0"),
        default=Decimal("0"),
    )

    maximum_days = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        allow_null=True,
    )

class LeaveRequestSerializer(
    serializers.ModelSerializer
):

    leave_type_name = serializers.CharField(
        source="leave_type.name",
        read_only=True,
    )

    approval_steps = (
        LeaveApprovalStepSerializer(
            many=True,
            read_only=True,
        )
    )

    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest

        fields = [
            "id",
            "employee",
            "employee_name",
            "leave_type",
            "leave_type_name",
            "start_date",
            "end_date",
            "requested_days",
            "reason",
            "status",
            "submitted_at",
            "reviewed_by",
            "reviewed_at",
            "review_comment",
            "cancelled_at",
            "created_at",
            "updated_at",
            "approval_steps",
        ]

        read_only_fields = [
            "id",
            "employee",
            "employee_name",
            "requested_days",
            "status",
            "submitted_at",
            "reviewed_by",
            "reviewed_at",
            "review_comment",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(str)
    def get_employee_name(self, obj):
        identity = getattr(
            obj.employee,
            "identity",
            None,
        )

        if identity is None:
            return str(obj.employee)

        return (
            f"{identity.first_name} "
            f"{identity.last_name}"
        ).strip()


class LeaveRequestCreateSerializer(
    serializers.Serializer
):

    leave_type = serializers.UUIDField()

    start_date = serializers.DateField()

    end_date = serializers.DateField()

    reason = serializers.CharField(
        required=False,
        allow_blank=True,
    )


class LeaveRequestReviewSerializer(
    serializers.Serializer
):

    review_comment = serializers.CharField(
        required=False,
        allow_blank=True,
    )

class LeaveTypeSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = LeaveType

        fields = [
            "id",
            "organization",
            "code",
            "name",
            "description",
            "is_paid",
            "requires_approval",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "organization",
            "created_at",
            "updated_at",
        ]

class LeaveTypeWriteSerializer(
    serializers.Serializer
):

    code = serializers.CharField(
        max_length=50,
    )

    name = serializers.CharField(
        max_length=100,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    is_paid = serializers.BooleanField(
        default=True,
    )

    requires_approval = serializers.BooleanField(
        default=True,
    )

class LeavePolicySerializer(
    serializers.ModelSerializer
):

    leave_type_name = serializers.CharField(
        source="leave_type.name",
        read_only=True,
    )

    prorate_for_new_hires = serializers.BooleanField(
        default=False,
    )

    class Meta:
        model = LeavePolicy

        fields = [
            "id",
            "organization",
            "leave_type",
            "leave_type_name",
            "days_per_year",
            "minimum_days_per_request",
            "maximum_days_per_request",
            "allow_half_day",
            "allow_carry_forward",
            "maximum_carry_forward_days",
            "prorate_for_new_hires",
            "requires_attachment",
            "accrual_enabled",
            "accrual_frequency",
            "accrual_start_month",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "organization",
            "leave_type_name",
            "created_at",
            "updated_at",
        ]


class LeavePolicyWriteSerializer(
    serializers.Serializer
):

    leave_type = serializers.UUIDField()

    days_per_year = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    minimum_days_per_request = (
        serializers.DecimalField(
            max_digits=6,
            decimal_places=2,
            default=0,
        )
    )

    maximum_days_per_request = (
        serializers.DecimalField(
            max_digits=6,
            decimal_places=2,
            required=False,
            allow_null=True,
        )
    )

    allow_half_day = serializers.BooleanField(
        default=False,
    )

    allow_carry_forward = (
        serializers.BooleanField(
            default=False,
        )
    )

    maximum_carry_forward_days = (
        serializers.DecimalField(
            max_digits=6,
            decimal_places=2,
            required=False,
            allow_null=True,
        )
    )

    requires_attachment = serializers.BooleanField(
        default=False,
    )

    prorate_for_new_hires = serializers.BooleanField(
        default=False,
    )

    accrual_enabled = serializers.BooleanField(
        default=False,
    )

    accrual_frequency = serializers.ChoiceField(
        choices=["ANNUAL", "MONTHLY"],
        default="ANNUAL",
    )

    accrual_start_month = serializers.IntegerField(
        default=1,
        min_value=1,
        max_value=12,
    )

class LeaveBalanceSerializer(
    serializers.ModelSerializer
):

    leave_type_name = serializers.CharField(
        source="leave_type.name",
        read_only=True,
    )

    employee_name = serializers.SerializerMethodField()

    accrued_days = (
        serializers.SerializerMethodField()
    )

    credit_adjustments = (
        serializers.SerializerMethodField()
    )

    debit_adjustments = (
        serializers.SerializerMethodField()
    )

    total_available_days = (
        serializers.SerializerMethodField()
    )

    remaining_days = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = LeaveBalance

        fields = [
            "id",
            "employee",
            "employee_name",

            "leave_type",
            "leave_type_name",

            "year",

            "entitlement_days",
            "accrual_enabled",
            "accrual_frequency",
            "accrued_days",
            "carry_forward_days",

            "credit_adjustments",
            "debit_adjustments",

            "total_available_days",
            "used_days",
            "remaining_days",

            "created_at",
            "updated_at",
        ]

        read_only_fields = fields
        
    @extend_schema_field(str)
    def get_employee_name(
        self,
        obj,
    ):

        identity = getattr(
            obj.employee,
            "identity",
            None,
        )

        if identity is None:
            return str(obj.employee)

        return (
            f"{identity.first_name} "
            f"{identity.last_name}"
        ).strip()

    @extend_schema_field(
        serializers.DecimalField(
            max_digits=6,
            decimal_places=2,
        )
    )
    def get_accrued_days(
        self,
        obj,
    ):
        return obj.accrued_days

    @extend_schema_field(
        serializers.DecimalField(
            max_digits=6,
            decimal_places=2,
        )
    )
    def get_credit_adjustments(
        self,
        obj,
    ):
        return obj.credit_adjustments

    @extend_schema_field(
        serializers.DecimalField(
            max_digits=6,
            decimal_places=2,
        )
    )
    def get_debit_adjustments(
        self,
        obj,
    ):
        return obj.debit_adjustments

    @extend_schema_field(
        serializers.DecimalField(
            max_digits=6,
            decimal_places=2,
        )
    )
    def get_total_available_days(
        self,
        obj,
    ):
        return obj.total_available_days

    @extend_schema_field(
        serializers.DecimalField(
            max_digits=6,
            decimal_places=2,
        )
    )
    def get_remaining_days(
        self,
        obj,
    ):
        return obj.remaining_days
        
         
class WorkScheduleSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = WorkSchedule

        fields = [
            "id",
            "organization",
            "code",
            "name",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "is_default",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "organization",
            "created_at",
            "updated_at",
        ]

class WorkScheduleWriteSerializer(
    serializers.Serializer
):

    code = serializers.CharField(
        max_length=50,
    )

    name = serializers.CharField(
        max_length=100,
    )

    monday = serializers.BooleanField(
        default=True,
    )

    tuesday = serializers.BooleanField(
        default=True,
    )

    wednesday = serializers.BooleanField(
        default=True,
    )

    thursday = serializers.BooleanField(
        default=True,
    )

    friday = serializers.BooleanField(
        default=True,
    )

    saturday = serializers.BooleanField(
        default=False,
    )

    sunday = serializers.BooleanField(
        default=False,
    )

    is_default = serializers.BooleanField(
        default=False,
    )

class PublicHolidaySerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = PublicHoliday

        fields = [
            "id",
            "organization",
            "date",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "organization",
            "created_at",
            "updated_at",
        ]

class PublicHolidayWriteSerializer(
    serializers.Serializer
):

    date = serializers.DateField()

    name = serializers.CharField(
        max_length=150,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

class EmployeeWorkScheduleSerializer(
    serializers.ModelSerializer
):

    work_schedule_name = serializers.CharField(
        source="work_schedule.name",
        read_only=True,
    )

    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeWorkSchedule

        fields = [
            "id",
            "employee",
            "employee_name",
            "work_schedule",
            "work_schedule_name",
            "effective_from",
            "effective_to",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "employee",
            "employee_name",
            "work_schedule_name",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_employee_name(self, obj):

        identity = getattr(
            obj.employee,
            "identity",
            None,
        )

        if identity is None:
            return str(obj.employee)

        return (
            f"{identity.first_name} "
            f"{identity.last_name}"
        ).strip()

class EmployeeWorkScheduleWriteSerializer(
    serializers.Serializer
):

    work_schedule = serializers.UUIDField()

    effective_from = serializers.DateField()

    effective_to = serializers.DateField(
        required=False,
        allow_null=True,
    )

class LeaveEntitlementSerializer(
    serializers.ModelSerializer
):

    employee_name = serializers.SerializerMethodField()

    leave_type_name = serializers.CharField(
        source="leave_type.name",
        read_only=True,
    )

    class Meta:
        model = LeaveEntitlement

        fields = [
            "id",
            "employee",
            "employee_name",
            "leave_type",
            "leave_type_name",
            "year",
            "days",
            "is_override",
            "reason",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "employee",
            "employee_name",
            "leave_type_name",
            "created_at",
            "updated_at",
        ]

    def get_employee_name(self, obj):

        identity = getattr(
            obj.employee,
            "identity",
            None,
        )

        if identity is None:
            return str(obj.employee)

        return (
            f"{identity.first_name} "
            f"{identity.last_name}"
        ).strip()


class LeaveEntitlementWriteSerializer(
    serializers.Serializer
):

    leave_type = serializers.UUIDField()

    year = serializers.IntegerField(
        min_value=2000,
    )

    days = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=0,
    )

    is_override = serializers.BooleanField(
        default=False,
    )

    reason = serializers.CharField(
        required=False,
        allow_blank=True,
    )

class LeaveBalanceAdjustmentSerializer(
    serializers.ModelSerializer
):

    adjusted_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalanceAdjustment

        fields = [
            "id",
            "balance",
            "amount",
            "adjustment_type",
            "reason",
            "adjusted_by",
            "adjusted_by_name",
            "adjusted_at",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "balance",
            "adjusted_by",
            "adjusted_by_name",
            "adjusted_at",
            "created_at",
        ]

    def get_adjusted_by_name(
        self,
        obj,
    ):
        return (
            f"{obj.adjusted_by.first_name} "
            f"{obj.adjusted_by.last_name}"
        ).strip()

class LeaveBalanceAdjustmentWriteSerializer(
    serializers.Serializer
):

    amount = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )

    adjustment_type = serializers.ChoiceField(
        choices=[
            "CREDIT",
            "DEBIT",
        ],
    )

    reason = serializers.CharField()


class LeaveAccrualSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = LeaveAccrual

        fields = [
            "id",
            "balance",
            "year",
            "period_month",
            "amount",
            "accrued_at",
            "created_at",
        ]

        read_only_fields = fields