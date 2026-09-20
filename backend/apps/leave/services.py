from django.db import transaction
from django.utils import timezone
from .models import (
    LeaveType,
    LeavePolicy,
    LeaveBalance,
    LeaveRequest,
    PublicHoliday,
    WorkSchedule,
    EmployeeWorkSchedule,
    LeaveEntitlement,
    LeaveBalanceAdjustment,
    LeaveAccrual,
)
from apps.access.models import OrganizationMembership
from decimal import Decimal
from datetime import (
    timedelta,
    date,
)
from decimal import (
    Decimal,
    ROUND_HALF_UP,
)

from django.db.models import Sum
from django.db.models import Q
from apps.employee.models import (
    Employee,
    Employment,
)
from django.db import transaction
from django.utils import timezone

from apps.employee.models import Employee
from apps.leave.models import (
    LeaveApprovalRule,
    LeaveApprovalStep,
)


class LeaveTypeService:

    @staticmethod
    @transaction.atomic
    def create_leave_type(
        *,
        organization,
        code,
        name,
        description="",
        is_paid=True,
        requires_approval=True,
    ):
        if LeaveType.objects.filter(
            organization=organization,
            code=code,
        ).exists():
            raise ValueError(
                "Leave type code already exists "
                "in this organization."
            )

        return LeaveType.objects.create(
            organization=organization,
            code=code,
            name=name,
            description=description,
            is_paid=is_paid,
            requires_approval=requires_approval,
        )

    @staticmethod
    @transaction.atomic
    def update_leave_type(
        *,
        leave_type,
        organization,
        code,
        name,
        description="",
        is_paid=True,
        requires_approval=True,
    ):
        if (
            leave_type.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave type does not belong "
                "to this organization."
            )

        duplicate = (
            LeaveType.objects
            .filter(
                organization=organization,
                code=code,
            )
            .exclude(
                id=leave_type.id,
            )
            .exists()
        )

        if duplicate:
            raise ValueError(
                "Leave type code already exists "
                "in this organization."
            )

        leave_type.code = code
        leave_type.name = name
        leave_type.description = description
        leave_type.is_paid = is_paid
        leave_type.requires_approval = (
            requires_approval
        )

        leave_type.save(
            update_fields=[
                "code",
                "name",
                "description",
                "is_paid",
                "requires_approval",
                "updated_at",
            ]
        )

        return leave_type

    @staticmethod
    @transaction.atomic
    def deactivate_leave_type(
        *,
        leave_type,
        organization,
    ):
        if (
            leave_type.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave type does not belong "
                "to this organization."
            )

        if not leave_type.is_active:
            raise ValueError(
                "Leave type is already inactive."
            )

        leave_type.is_active = False

        leave_type.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return leave_type

    @staticmethod
    @transaction.atomic
    def activate_leave_type(
        *,
        leave_type,
        organization,
    ):
        if (
            leave_type.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave type does not belong "
                "to this organization."
            )

        if leave_type.is_active:
            raise ValueError(
                "Leave type is already active."
            )

        leave_type.is_active = True

        leave_type.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return leave_type


class LeavePolicyService:

    @staticmethod
    @transaction.atomic
    def create_policy(
        *,
        organization,
        leave_type,
        days_per_year,
        minimum_days_per_request=0,
        maximum_days_per_request=None,
        allow_half_day=False,
        allow_carry_forward=False,
        maximum_carry_forward_days=None,
        requires_attachment=False,
        prorate_for_new_hires=False,
        accrual_enabled=False,
        accrual_frequency="ANNUAL",
        accrual_start_month=1,
    ):
        if leave_type.organization_id != organization.id:
            raise ValueError(
                "Leave type does not belong "
                "to this organization."
            )

        if LeavePolicy.objects.filter(
            organization=organization,
            leave_type=leave_type,
        ).exists():
            raise ValueError(
                "A leave policy already exists "
                "for this leave type."
            )

        if days_per_year < 0:
            raise ValueError(
                "Days per year cannot be negative."
            )

        if (
            maximum_days_per_request is not None
            and minimum_days_per_request
            > maximum_days_per_request
        ):
            raise ValueError(
                "Minimum request days cannot exceed "
                "maximum request days."
            )

        if (
            not allow_carry_forward
            and maximum_carry_forward_days
            not in [None, 0]
        ):
            raise ValueError(
                "Maximum carry-forward days cannot "
                "be set when carry-forward is disabled."
            )

        if accrual_frequency not in {"ANNUAL", "MONTHLY"}:
            raise ValueError(
                "Invalid accrual frequency."
            )

        if not 1 <= accrual_start_month <= 12:
            raise ValueError(
                "Accrual start month must be between 1 and 12."
            )

        return LeavePolicy.objects.create(
            organization=organization,
            leave_type=leave_type,
            days_per_year=days_per_year,
            minimum_days_per_request=(
                minimum_days_per_request
            ),
            maximum_days_per_request=(
                maximum_days_per_request
            ),
            allow_half_day=allow_half_day,
            allow_carry_forward=allow_carry_forward,
            maximum_carry_forward_days=(
                maximum_carry_forward_days
            ),
            requires_attachment=requires_attachment,
            prorate_for_new_hires=(
                prorate_for_new_hires
            ),
            accrual_enabled=accrual_enabled,
            accrual_frequency=accrual_frequency,
            accrual_start_month=accrual_start_month,
        )


    @staticmethod
    @transaction.atomic
    def update_policy(
        *,
        policy,
        organization,
        days_per_year,
        minimum_days_per_request=0,
        maximum_days_per_request=None,
        allow_half_day=False,
        allow_carry_forward=False,
        maximum_carry_forward_days=None,
        requires_attachment=False,
        prorate_for_new_hires=False,
        accrual_enabled=False,
        accrual_frequency="ANNUAL",
        accrual_start_month=1,
    ):
        if (
            policy.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave policy does not belong "
                "to this organization."
            )

        if days_per_year < 0:
            raise ValueError(
                "Days per year cannot be negative."
            )

        if (
            maximum_days_per_request is not None
            and minimum_days_per_request
            > maximum_days_per_request
        ):
            raise ValueError(
                "Minimum request days cannot exceed "
                "maximum request days."
            )

        if (
            not allow_carry_forward
            and maximum_carry_forward_days
            not in [None, 0]
        ):
            raise ValueError(
                "Maximum carry-forward days cannot "
                "be set when carry-forward is disabled."
            )

        if (
            maximum_carry_forward_days is not None
            and maximum_carry_forward_days < 0
        ):
            raise ValueError(
                "Maximum carry-forward days cannot "
                "be negative."
            )

        if accrual_frequency not in {"ANNUAL", "MONTHLY"}:
            raise ValueError(
                "Invalid accrual frequency."
            )

        if not 1 <= accrual_start_month <= 12:
            raise ValueError(
                "Accrual start month must be between 1 and 12."
            )

        policy.days_per_year = days_per_year
        policy.minimum_days_per_request = (
            minimum_days_per_request
        )
        policy.maximum_days_per_request = (
            maximum_days_per_request
        )
        policy.allow_half_day = allow_half_day
        policy.allow_carry_forward = (
            allow_carry_forward
        )
        policy.maximum_carry_forward_days = (
            maximum_carry_forward_days
        )
        policy.requires_attachment = (
            requires_attachment
        )
        policy.prorate_for_new_hires = (
            prorate_for_new_hires
        )
        policy.accrual_enabled = accrual_enabled
        policy.accrual_frequency = accrual_frequency
        policy.accrual_start_month = accrual_start_month

        policy.save(
            update_fields=[
                "days_per_year",
                "minimum_days_per_request",
                "maximum_days_per_request",
                "allow_half_day",
                "allow_carry_forward",
                "maximum_carry_forward_days",
                "requires_attachment",
                "prorate_for_new_hires",
                "accrual_enabled",
                "accrual_frequency",
                "accrual_start_month",
                "updated_at",
            ]
        )

        return policy

    @staticmethod
    @transaction.atomic
    def deactivate_policy(
        *,
        policy,
        organization,
    ):
        if (
            policy.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave policy does not belong "
                "to this organization."
            )
    
        if not policy.is_active:
            raise ValueError(
                "Leave policy is already inactive."
            )
    
        policy.is_active = False
    
        policy.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )
    
        return policy
    
    
    @staticmethod
    @transaction.atomic
    def activate_policy(
        *,
        policy,
        organization,
    ):
        if (
            policy.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave policy does not belong "
                "to this organization."
            )
    
        if policy.is_active:
            raise ValueError(
                "Leave policy is already active."
            )
    
        # -----------------------------------
        # An organization can only have one
        # active policy for a leave type
        # -----------------------------------
    
        active_policy_exists = (
            LeavePolicy.objects
            .filter(
                organization=organization,
                leave_type=policy.leave_type,
                is_active=True,
            )
            .exclude(
                id=policy.id,
            )
            .exists()
        )
    
        if active_policy_exists:
            raise ValueError(
                "Another active leave policy already "
                "exists for this leave type."
            )
    
        policy.is_active = True
    
        policy.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )
    
        return policy
    

class LeaveBalanceService:

    @staticmethod
    @transaction.atomic
    def create_balance(
        *,
        employee,
        leave_type,
        year,
        entitlement_days,
        carry_forward_days=Decimal("0"),
    ):
        # -----------------------------------
        # Organization validation
        # -----------------------------------

        if (
            employee.organization_id
            != leave_type.organization_id
        ):
            raise ValueError(
                "Leave type does not belong "
                "to the employee's organization."
            )

        # -----------------------------------
        # Policy validation
        # -----------------------------------

        try:
            policy = (
                leave_type.policies
                .get(
                    is_active=True,
                )
            )

        except LeavePolicy.DoesNotExist:
            raise ValueError(
                "No active leave policy exists "
                "for this leave type."
            )

        # -----------------------------------
        # Carry-forward validation
        # -----------------------------------

        if carry_forward_days < 0:
            raise ValueError(
                "Carry-forward days cannot be negative."
            )

        if (
            carry_forward_days > 0
            and not policy.allow_carry_forward
        ):
            raise ValueError(
                "Carry-forward is not allowed "
                "for this leave type."
            )

        if (
            policy.maximum_carry_forward_days is not None
            and carry_forward_days
            > policy.maximum_carry_forward_days
        ):
            raise ValueError(
                "Carry-forward exceeds the "
                "allowed maximum."
            )

        # -----------------------------------
        # Entitlement validation
        # -----------------------------------

        if entitlement_days < 0:
            raise ValueError(
                "Entitlement days cannot be negative."
            )

        # Leave policy limit
        if entitlement_days > policy.days_per_year:
            raise ValueError(
                "Entitlement exceeds the leave "
                "policy allowance."
            )

        # -----------------------------------
        # Duplicate balance
        # -----------------------------------

        if LeaveBalance.objects.filter(
            employee=employee,
            leave_type=leave_type,
            year=year,
        ).exists():
            raise ValueError(
                "A leave balance already exists "
                "for this employee, leave type, and year."
            )

        # -----------------------------------
        # Create balance
        # -----------------------------------

        return LeaveBalance.objects.create(
            employee=employee,
            leave_type=leave_type,
            year=year,
            entitlement_days=entitlement_days,
            carry_forward_days=carry_forward_days,
            accrual_enabled=policy.accrual_enabled,
            accrual_frequency=policy.accrual_frequency,
        )

    @staticmethod
    def get_balance(
        *,
        employee,
        leave_type,
        year,
    ):
        return LeaveBalance.objects.get(
            employee=employee,
            leave_type=leave_type,
            year=year,
        )
    
    @staticmethod
    def get_remaining_days(
        *,
        employee,
        leave_type,
        year,
    ):
        balance = (
            LeaveBalanceService.get_balance(
                employee=employee,
                leave_type=leave_type,
                year=year,
            )
        )
    
        return balance.remaining_days



    @staticmethod
    def get_pending_days(
        *,
        employee,
        leave_type,
        year,
    ):
        pending = (
            LeaveRequest.objects
            .filter(
                employee=employee,
                leave_type=leave_type,
                status=LeaveRequest.Status.SUBMITTED,
                start_date__year=year,
            )
        )

        return sum(
            (
                request.requested_days
                for request in pending
            ),
            Decimal("0"),
        )

    @staticmethod
    def get_available_days(
        *,
        employee,
        leave_type,
        year,
    ):
        balance = (
            LeaveBalanceService.get_balance(
                employee=employee,
                leave_type=leave_type,
                year=year,
            )
        )

        pending_days = (
            LeaveBalanceService
            .get_pending_days(
                employee=employee,
                leave_type=leave_type,
                year=year,
            )
        )

        return max(
            balance.remaining_days
            - pending_days,
            Decimal("0"),
        )


    @staticmethod
    @transaction.atomic
    def initialize_year(
        *,
        organization,
        year,
    ):
        active_employees = (
            Employee.objects
            .filter(
                organization=organization,
                is_active=True,
            )
        )

        active_policies = (
            LeavePolicy.objects
            .filter(
                organization=organization,
                is_active=True,
                leave_type__is_active=True,
            )
            .select_related(
                "leave_type",
            )
        )

        created_balances = []

        for employee in active_employees:

            for policy in active_policies:

                previous_balance = (
                    LeaveBalance.objects
                    .filter(
                        employee=employee,
                        leave_type=policy.leave_type,
                        year=year - 1,
                    )
                    .first()
                )

                carry_forward_days = Decimal("0")

                if previous_balance:
                    carry_forward_days = (
                        LeaveBalanceService
                        .calculate_carry_forward(
                            previous_balance=previous_balance,
                            policy=policy,
                        )
                    )

                balance, created = (
                    LeaveBalance.objects.get_or_create(
                        employee=employee,
                        leave_type=policy.leave_type,
                        year=year,
                        defaults={
                            "entitlement_days": (
                                LeaveEntitlementService
                                .get_effective_days(
                                    employee=employee,
                                    leave_type=policy.leave_type,
                                    year=year,
                                )
                            ),
                            "carry_forward_days": (
                                carry_forward_days
                            ),
                            "used_days": Decimal("0"),
                        },
                    )
                )

                if created:
                    created_balances.append(
                        balance
                    )

        return created_balances


    @staticmethod
    def calculate_carry_forward(
        *,
        previous_balance,
        policy,
    ):
        if not policy.allow_carry_forward:
            return Decimal("0")

        previous_remaining = (
            previous_balance.remaining_days
        )

        if (
            policy.maximum_carry_forward_days
            is not None
        ):
            previous_remaining = min(
                previous_remaining,
                policy.maximum_carry_forward_days,
            )

        return max(
            previous_remaining,
            Decimal("0"),
        )

class LeaveRequestService:

    @staticmethod
    @transaction.atomic
    def create_request(
        *,
        employee,
        leave_type,
        organization,
        start_date,
        end_date,
        reason="",
    ):

        # -----------------------------------
        # Employee organization validation
        # -----------------------------------

        if (
            employee.organization_id
            != organization.id
        ):
            raise ValueError(
                "Employee does not belong "
                "to this organization."
            )

        # -----------------------------------
        # Leave type organization validation
        # -----------------------------------

        if (
            leave_type.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave type does not belong "
                "to this organization."
            )

        # -----------------------------------
        # Leave type must be active
        # -----------------------------------

        if not leave_type.is_active:
            raise ValueError(
                "Leave type is inactive."
            )

        # -----------------------------------
        # Active policy
        # -----------------------------------

        try:
            policy = (
                leave_type.policies
                .get(
                    is_active=True,
                )
            )

        except LeavePolicy.DoesNotExist:
            raise ValueError(
                "No active leave policy exists "
                "for this leave type."
            )

        # -----------------------------------
        # Calculate working days
        # -----------------------------------

        requested_days = (
            LeaveRequestService
            .calculate_requested_days(
                employee=employee,
                start_date=start_date,
                end_date=end_date,
            )
        )

        # -----------------------------------
        # Policy minimum
        # -----------------------------------

        if (
            requested_days
            < policy.minimum_days_per_request
        ):
            raise ValueError(
                "Requested leave is below "
                "the policy minimum."
            )

        # -----------------------------------
        # Policy maximum
        # -----------------------------------

        if (
            policy.maximum_days_per_request
            is not None
            and requested_days
            > policy.maximum_days_per_request
        ):
            raise ValueError(
                "Requested leave exceeds "
                "the policy maximum."
            )

        # -----------------------------------
        # Overlapping requests
        # -----------------------------------

        overlapping = (
            LeaveRequest.objects
            .filter(
                employee=employee,
                start_date__lte=end_date,
                end_date__gte=start_date,
            )
            .exclude(
                status__in=[
                    LeaveRequest.Status.REJECTED,
                    LeaveRequest.Status.CANCELLED,
                ]
            )
            .exists()
        )

        if overlapping:
            raise ValueError(
                "Employee already has an overlapping "
                "leave request."
            )

        # -----------------------------------
        # Create draft request
        # -----------------------------------

        return LeaveRequest.objects.create(
            employee=employee,
            leave_type=leave_type,
            organization=organization,
            start_date=start_date,
            end_date=end_date,
            requested_days=requested_days,
            reason=reason,
        )

    @staticmethod
    @transaction.atomic
    def submit_request(
        *,
        leave_request,
        organization,
    ):
        if (
            leave_request.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave request does not belong "
                "to this organization."
            )

        if not leave_request.employee.is_active:
            raise ValueError(
                "Inactive employees cannot submit "
                "leave requests."
            )

        if (
            leave_request.status
            != LeaveRequest.Status.DRAFT
        ):
            raise ValueError(
                "Only draft leave requests "
                "can be submitted."
            )

        available_days = (
            LeaveBalanceService
            .get_available_days(
                employee=leave_request.employee,
                leave_type=leave_request.leave_type,
                year=leave_request.start_date.year,
            )
        )

        if (
            available_days
            < leave_request.requested_days
        ):
            raise ValueError(
                "Employee does not have enough "
                "available leave balance."
            )

        leave_request.status = (
            LeaveRequest.Status.SUBMITTED
        )

        leave_request.submitted_at = (
            timezone.now()
        )

        leave_request.save(
            update_fields=[
                "status",
                "submitted_at",
                "updated_at",
            ]
        )

        # Leave types that do not require approval
        # are approved immediately.
        if not leave_request.leave_type.requires_approval:
            return (
                LeaveRequestService
                ._finalize_approval(
                    leave_request=leave_request,
                )
            )

        # If approval rules exist, snapshot the
        # manager hierarchy onto this request.
        LeaveApprovalService.create_approval_steps(
            leave_request=leave_request,
            organization=organization,
        )

        return leave_request

    @staticmethod
    @transaction.atomic
    def approve_request(
        *,
        leave_request,
        reviewed_by,
        organization,
        review_comment="",
    ):
        leave_request = (
            LeaveRequest.objects
            .select_for_update()
            .select_related(
                "employee",
                "leave_type",
            )
            .get(
                id=leave_request.id,
            )
        )

        if (
            leave_request.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave request does not belong "
                "to this organization."
            )

        if (
            leave_request.status
            != LeaveRequest.Status.SUBMITTED
        ):
            raise ValueError(
                "Only submitted leave requests "
                "can be approved."
            )

        reviewer_membership = (
            OrganizationMembership.objects.filter(
                user=reviewed_by,
                organization=organization,
                is_active=True,
            )
            .first()
        )

        if reviewer_membership is None:
            raise ValueError(
                "Reviewer does not belong "
                "to this organization."
            )

        has_chain = (
            LeaveApprovalService
            .has_approval_chain(
                leave_request=leave_request,
            )
        )

        if not has_chain:
            return (
                LeaveRequestService
                ._finalize_approval(
                    leave_request=leave_request,
                    reviewed_by=reviewed_by,
                    review_comment=review_comment,
                )
            )

        LeaveApprovalService.approve_current_step(
            leave_request=leave_request,
            user=reviewed_by,
            comment=review_comment,
        )

        current_step = (
            LeaveApprovalService
            .get_current_step(
                leave_request=leave_request,
                lock=True,
            )
        )

        # More approval levels remain.
        if current_step is not None:
            return leave_request

        # Final approval level has just approved.
        return (
            LeaveRequestService
            ._finalize_approval(
                leave_request=leave_request,
                reviewed_by=reviewed_by,
                review_comment=review_comment,
            )
        )


    @staticmethod
    @transaction.atomic
    def reject_request(
        *,
        leave_request,
        reviewed_by,
        organization,
        review_comment="",
    ):
        leave_request = (
            LeaveRequest.objects
            .select_for_update()
            .select_related(
                "employee",
                "leave_type",
            )
            .get(
                id=leave_request.id,
            )
        )

        if (
            leave_request.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave request does not belong "
                "to this organization."
            )

        if (
            leave_request.status
            != LeaveRequest.Status.SUBMITTED
        ):
            raise ValueError(
                "Only submitted leave requests "
                "can be rejected."
            )

        reviewer_membership = (
            OrganizationMembership.objects.filter(
                user=reviewed_by,
                organization=organization,
                is_active=True,
            )
            .first()
        )

        if reviewer_membership is None:
            raise ValueError(
                "Reviewer does not belong "
                "to this organization."
            )

        has_chain = (
            LeaveApprovalService
            .has_approval_chain(
                leave_request=leave_request,
            )
        )

        if has_chain:

            LeaveApprovalService.reject_current_step(
                leave_request=leave_request,
                user=reviewed_by,
                comment=review_comment,
            )

        leave_request.status = (
            LeaveRequest.Status.REJECTED
        )

        leave_request.reviewed_by = (
            reviewed_by
        )

        leave_request.reviewed_at = (
            timezone.now()
        )

        leave_request.review_comment = (
            review_comment
        )

        leave_request.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "review_comment",
                "updated_at",
            ]
        )

        return leave_request


    @staticmethod
    @transaction.atomic
    def cancel_request(
        *,
        leave_request,
    ):
        leave_request = (
            LeaveRequest.objects
            .select_for_update()
            .select_related(
                "employee",
                "leave_type",
            )
            .get(
                id=leave_request.id,
            )
        )

        if (
            leave_request.status
            not in [
                LeaveRequest.Status.SUBMITTED,
                LeaveRequest.Status.APPROVED,
            ]
        ):
            raise ValueError(
                "Only submitted or approved leave "
                "requests can be cancelled."
            )

        if (
            leave_request.status
            == LeaveRequest.Status.APPROVED
        ):
            balance = (
                LeaveBalance.objects
                .select_for_update()
                .get(
                    employee=leave_request.employee,
                    leave_type=leave_request.leave_type,
                    year=leave_request.start_date.year,
                )
            )

            balance.used_days = max(
                balance.used_days
                - leave_request.requested_days,
                Decimal("0"),
            )

            balance.save(
                update_fields=[
                    "used_days",
                    "updated_at",
                ]
            )

        leave_request.status = (
            LeaveRequest.Status.CANCELLED
        )

        leave_request.cancelled_at = (
            timezone.now()
        )

        leave_request.save(
            update_fields=[
                "status",
                "cancelled_at",
                "updated_at",
            ]
        )

        return leave_request

        
    @staticmethod
    def calculate_requested_days(
        *,
        employee,
        start_date,
        end_date,
    ):
        return (
            LeaveCalendarService
            .calculate_employee_working_days(
                employee=employee,
                start_date=start_date,
                end_date=end_date,
            )
        )

    @staticmethod
    def _finalize_approval(
        *,
        leave_request,
        reviewed_by=None,
        review_comment="",
    ):
        balance = (
            LeaveBalance.objects
            .select_for_update()
            .get(
                employee=leave_request.employee,
                leave_type=leave_request.leave_type,
                year=leave_request.start_date.year,
            )
        )

        if (
            balance.remaining_days
            < leave_request.requested_days
        ):
            raise ValueError(
                "Employee does not have enough "
                "leave balance."
            )

        balance.used_days += (
            leave_request.requested_days
        )

        balance.save(
            update_fields=[
                "used_days",
                "updated_at",
            ]
        )

        leave_request.status = (
            LeaveRequest.Status.APPROVED
        )

        leave_request.reviewed_by = (
            reviewed_by
        )

        leave_request.reviewed_at = (
            timezone.now()
        )

        leave_request.review_comment = (
            review_comment or ""
        )

        leave_request.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "review_comment",
                "updated_at",
            ]
        )

        return leave_request

class LeaveCalendarService:

    WEEKDAY_FIELDS = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday",
        5: "saturday",
        6: "sunday",
    }

    @staticmethod
    def is_working_day(
        *,
        organization,
        work_schedule,
        day,
    ):
        if (
            work_schedule.organization_id
            != organization.id
        ):
            raise ValueError(
                "Work schedule does not belong "
                "to this organization."
            )

        if not work_schedule.is_active:
            raise ValueError(
                "Work schedule is inactive."
            )

        weekday_field = (
            LeaveCalendarService
            .WEEKDAY_FIELDS[day.weekday()]
        )

        if not getattr(
            work_schedule,
            weekday_field,
        ):
            return False

        holiday_exists = (
            PublicHoliday.objects
            .filter(
                organization=organization,
                date=day,
                is_active=True,
            )
            .exists()
        )

        if holiday_exists:
            return False

        return True

    @staticmethod
    def calculate_working_days(
        *,
        organization,
        work_schedule,
        start_date,
        end_date,
    ):
        if end_date < start_date:
            raise ValueError(
                "End date cannot be before start date."
            )

        total = 0

        current_date = start_date

        while current_date <= end_date:

            if LeaveCalendarService.is_working_day(
                organization=organization,
                work_schedule=work_schedule,
                day=current_date,
            ):
                total += 1

            current_date += timedelta(
                days=1,
            )

        return Decimal(total)

    @staticmethod
    def calculate_employee_working_days(
        *,
        employee,
        start_date,
        end_date,
    ):
        if end_date < start_date:
            raise ValueError(
                "End date cannot be before start date."
            )

        total = 0
        current_date = start_date

        while current_date <= end_date:

            work_schedule = (
                EmployeeWorkScheduleService
                .get_schedule_for_date(
                    employee=employee,
                    day=current_date,
                )
            )

            if (
                LeaveCalendarService
                .is_working_day(
                    organization=employee.organization,
                    work_schedule=work_schedule,
                    day=current_date,
                )
            ):
                total += 1

            current_date += timedelta(
                days=1,
            )

        return Decimal(total)


class WorkScheduleService:

    @staticmethod
    @transaction.atomic
    def create_schedule(
        *,
        organization,
        code,
        name,
        monday=True,
        tuesday=True,
        wednesday=True,
        thursday=True,
        friday=True,
        saturday=False,
        sunday=False,
        is_default=False,
    ):
        if WorkSchedule.objects.filter(
            organization=organization,
            code=code,
        ).exists():
            raise ValueError(
                "Work schedule code already exists "
                "in this organization."
            )

        if is_default:
            WorkSchedule.objects.filter(
                organization=organization,
                is_default=True,
            ).update(
                is_default=False,
            )

        return WorkSchedule.objects.create(
            organization=organization,
            code=code,
            name=name,
            monday=monday,
            tuesday=tuesday,
            wednesday=wednesday,
            thursday=thursday,
            friday=friday,
            saturday=saturday,
            sunday=sunday,
            is_default=is_default,
        )

    @staticmethod
    def get_default_schedule(
        *,
        organization,
    ):
        try:
            return WorkSchedule.objects.get(
                organization=organization,
                is_default=True,
                is_active=True,
            )
        except WorkSchedule.DoesNotExist:
            raise ValueError(
                "No active default work schedule exists "
                "for this organization."
            )

    @staticmethod
    @transaction.atomic
    def update_schedule(
        *,
        schedule,
        organization,
        code,
        name,
        monday=True,
        tuesday=True,
        wednesday=True,
        thursday=True,
        friday=True,
        saturday=False,
        sunday=False,
        is_default=False,
    ):
        if (
            schedule.organization_id
            != organization.id
        ):
            raise ValueError(
                "Work schedule does not belong "
                "to this organization."
            )

        duplicate = (
            WorkSchedule.objects
            .filter(
                organization=organization,
                code=code,
            )
            .exclude(
                id=schedule.id,
            )
            .exists()
        )

        if duplicate:
            raise ValueError(
                "Work schedule code already exists "
                "in this organization."
            )

        if is_default:
            WorkSchedule.objects.filter(
                organization=organization,
                is_default=True,
            ).exclude(
                id=schedule.id,
            ).update(
                is_default=False,
            )

        schedule.code = code
        schedule.name = name
        schedule.monday = monday
        schedule.tuesday = tuesday
        schedule.wednesday = wednesday
        schedule.thursday = thursday
        schedule.friday = friday
        schedule.saturday = saturday
        schedule.sunday = sunday
        schedule.is_default = is_default

        schedule.save(
            update_fields=[
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
                "updated_at",
            ]
        )

        return schedule

    @staticmethod
    @transaction.atomic
    def activate_schedule(
        *,
        schedule,
        organization,
    ):
        if (
            schedule.organization_id
            != organization.id
        ):
            raise ValueError(
                "Work schedule does not belong "
                "to this organization."
            )

        if schedule.is_active:
            raise ValueError(
                "Work schedule is already active."
            )

        schedule.is_active = True

        schedule.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return schedule

    @staticmethod
    @transaction.atomic
    def deactivate_schedule(
        *,
        schedule,
        organization,
    ):
        if (
            schedule.organization_id
            != organization.id
        ):
            raise ValueError(
                "Work schedule does not belong "
                "to this organization."
            )

        if not schedule.is_active:
            raise ValueError(
                "Work schedule is already inactive."
            )

        if schedule.is_default:
            raise ValueError(
                "The default work schedule must be "
                "changed before this schedule can "
                "be deactivated."
            )

        schedule.is_active = False

        schedule.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return schedule

    @staticmethod
    @transaction.atomic
    def set_default_schedule(
        *,
        schedule,
        organization,
    ):
        if (
            schedule.organization_id
            != organization.id
        ):
            raise ValueError(
                "Work schedule does not belong "
                "to this organization."
            )

        if not schedule.is_active:
            raise ValueError(
                "An inactive work schedule cannot "
                "be the default."
            )

        WorkSchedule.objects.filter(
            organization=organization,
            is_default=True,
        ).exclude(
            id=schedule.id,
        ).update(
            is_default=False,
        )

        schedule.is_default = True

        schedule.save(
            update_fields=[
                "is_default",
                "updated_at",
            ]
        )

        return schedule


class PublicHolidayService:

    @staticmethod
    @transaction.atomic
    def create_holiday(
        *,
        organization,
        date,
        name,
        description="",
    ):
        if PublicHoliday.objects.filter(
            organization=organization,
            date=date,
        ).exists():
            raise ValueError(
                "A public holiday already exists "
                "for this date."
            )

        return PublicHoliday.objects.create(
            organization=organization,
            date=date,
            name=name,
            description=description,
        )

    @staticmethod
    @transaction.atomic
    def update_holiday(
        *,
        holiday,
        organization,
        date,
        name,
        description="",
    ):
        if (
            holiday.organization_id
            != organization.id
        ):
            raise ValueError(
                "Public holiday does not belong "
                "to this organization."
            )
    
        duplicate = (
            PublicHoliday.objects
            .filter(
                organization=organization,
                date=date,
            )
            .exclude(
                id=holiday.id,
            )
            .exists()
        )
    
        if duplicate:
            raise ValueError(
                "A public holiday already exists "
                "for this date."
            )
    
        holiday.date = date
        holiday.name = name
        holiday.description = description
    
        holiday.save(
            update_fields=[
                "date",
                "name",
                "description",
                "updated_at",
            ]
        )
    
        return holiday
    
    @staticmethod
    @transaction.atomic
    def activate_holiday(
        *,
        holiday,
        organization,
    ):
        if (
            holiday.organization_id
            != organization.id
        ):
            raise ValueError(
                "Public holiday does not belong "
                "to this organization."
            )
    
        if holiday.is_active:
            raise ValueError(
                "Public holiday is already active."
            )
    
        holiday.is_active = True
    
        holiday.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )
    
        return holiday
    
    @staticmethod
    @transaction.atomic
    def deactivate_holiday(
        *,
        holiday,
        organization,
    ):
        if (
            holiday.organization_id
            != organization.id
        ):
            raise ValueError(
                "Public holiday does not belong "
                "to this organization."
            )
    
        if not holiday.is_active:
            raise ValueError(
                "Public holiday is already inactive."
            )
    
        holiday.is_active = False
    
        holiday.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )
    
        return holiday

class EmployeeWorkScheduleService:

    @staticmethod
    @transaction.atomic
    def assign_schedule(
        *,
        employee,
        work_schedule,
        effective_from,
        effective_to=None,
    ):
        # -----------------------------------
        # Organization validation
        # -----------------------------------

        if (
            employee.organization_id
            != work_schedule.organization_id
        ):
            raise ValueError(
                "Work schedule does not belong "
                "to the employee's organization."
            )

        # -----------------------------------
        # Date validation
        # -----------------------------------

        if (
            effective_to is not None
            and effective_to < effective_from
        ):
            raise ValueError(
                "Effective end date cannot be "
                "before the effective start date."
            )

        # -----------------------------------
        # Check overlapping assignments
        # -----------------------------------

        overlapping = (
            EmployeeWorkSchedule.objects
            .filter(
                employee=employee,
                is_active=True,
                effective_from__lte=(
                    effective_to
                    if effective_to is not None
                    else date.max
                ),
            )
            .filter(
                Q(
                    effective_to__isnull=True,
                )
                | Q(
                    effective_to__gte=effective_from,
                )
            )
            .exists()
        )

        if overlapping:
            raise ValueError(
                "The employee already has an "
                "overlapping work schedule."
            )

        return EmployeeWorkSchedule.objects.create(
            employee=employee,
            work_schedule=work_schedule,
            effective_from=effective_from,
            effective_to=effective_to,
        )

    @staticmethod
    def get_schedule_for_date(
        *,
        employee,
        day,
    ):
        assignment = (
            EmployeeWorkSchedule.objects
            .filter(
                employee=employee,
                is_active=True,
                effective_from__lte=day,
            )
            .filter(
                Q(
                    effective_to__isnull=True,
                )
                | Q(
                    effective_to__gte=day,
                )
            )
            .select_related(
                "work_schedule",
            )
            .order_by(
                "-effective_from",
            )
            .first()
        )

        if assignment:
            return assignment.work_schedule

        return (
            WorkScheduleService
            .get_default_schedule(
                organization=employee.organization,
            )
        ) 

    @staticmethod
    @transaction.atomic
    def update_assignment(
        *,
        assignment,
        employee,
        work_schedule,
        effective_from,
        effective_to=None,
    ):
        if assignment.employee_id != employee.id:
            raise ValueError(
                "Work schedule assignment does not belong "
                "to this employee."
            )

        if (
            employee.organization_id
            != work_schedule.organization_id
        ):
            raise ValueError(
                "Work schedule does not belong "
                "to the employee's organization."
            )

        if (
            effective_to is not None
            and effective_to < effective_from
        ):
            raise ValueError(
                "Effective end date cannot be "
                "before the effective start date."
            )

        overlapping = (
            EmployeeWorkSchedule.objects
            .filter(
                employee=employee,
                is_active=True,
            )
            .exclude(
                id=assignment.id,
            )
            .filter(
                effective_from__lte=(
                    effective_to
                    if effective_to is not None
                    else date.max
                )
            )
            .filter(
                Q(
                    effective_to__isnull=True,
                )
                | Q(
                    effective_to__gte=effective_from,
                )
            )
            .exists()
        )

        if overlapping:
            raise ValueError(
                "The employee already has an "
                "overlapping work schedule."
            )

        assignment.work_schedule = work_schedule
        assignment.effective_from = effective_from
        assignment.effective_to = effective_to

        assignment.save(
            update_fields=[
                "work_schedule",
                "effective_from",
                "effective_to",
                "updated_at",
            ]
        )

        return assignment

    @staticmethod
    @transaction.atomic
    def activate_assignment(
        *,
        assignment,
        employee,
    ):
        if assignment.employee_id != employee.id:
            raise ValueError(
                "Work schedule assignment does not belong "
                "to this employee."
            )

        if assignment.is_active:
            raise ValueError(
                "Work schedule assignment is already active."
            )

        assignment.is_active = True

        assignment.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return assignment

    @staticmethod
    @transaction.atomic
    def deactivate_assignment(
        *,
        assignment,
        employee,
    ):
        if assignment.employee_id != employee.id:
            raise ValueError(
                "Work schedule assignment does not belong "
                "to this employee."
            )

        if not assignment.is_active:
            raise ValueError(
                "Work schedule assignment is already inactive."
            )

        assignment.is_active = False

        assignment.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return assignment

class LeaveEntitlementService:

    @staticmethod
    @transaction.atomic
    def create_entitlement(
        *,
        employee,
        leave_type,
        year,
        days,
        is_override=False,
        reason="",
    ):
        if (
            employee.organization_id
            != leave_type.organization_id
        ):
            raise ValueError(
                "Leave type does not belong "
                "to the employee's organization."
            )

        if days < 0:
            raise ValueError(
                "Entitlement days cannot be negative."
            )

        if LeaveEntitlement.objects.filter(
            employee=employee,
            leave_type=leave_type,
            year=year,
        ).exists():
            raise ValueError(
                "An entitlement already exists "
                "for this employee, leave type, and year."
            )

        return LeaveEntitlement.objects.create(
            employee=employee,
            leave_type=leave_type,
            year=year,
            days=days,
            is_override=is_override,
            reason=reason,
        )


    @staticmethod
    def get_entitlement(
        *,
        employee,
        leave_type,
        year,
    ):
        try:
            return LeaveEntitlement.objects.get(
                employee=employee,
                leave_type=leave_type,
                year=year,
            )
        except LeaveEntitlement.DoesNotExist:
            return None


    @staticmethod
    def get_effective_days(
        *,
        employee,
        leave_type,
        year,
    ):
        entitlement = (
            LeaveEntitlementService
            .get_entitlement(
                employee=employee,
                leave_type=leave_type,
                year=year,
            )
        )

        if entitlement is not None:
            return entitlement.days

        try:
            policy = (
                leave_type.policies
                .get(
                    organization=employee.organization,
                    is_active=True,
                )
            )

        except LeavePolicy.DoesNotExist:
            raise ValueError(
                "No active leave policy exists "
                "for this leave type."
            )

        annual_days = policy.days_per_year

        if not policy.prorate_for_new_hires:
            return annual_days

        start_date = (
            LeaveEntitlementService
            .get_employment_start_date(
                employee=employee,
            )
        )

        if start_date is None:
            return annual_days

        return (
            LeaveEntitlementService
            .calculate_prorated_days(
                annual_days=annual_days,
                start_date=start_date,
                year=year,
            )
        )


    @staticmethod
    def prorate_entitlement(
        *,
        annual_days,
        start_date,
        year,
    ):
        if start_date.year > year:
            return Decimal("0")

        if start_date.year < year:
            return Decimal(annual_days)

        months_remaining = (
            12 - start_date.month + 1
        )

        return (
            Decimal(annual_days)
            * Decimal(months_remaining)
            / Decimal("12")
        ).quantize(
            Decimal("0.01")
        )

    @staticmethod
    @transaction.atomic
    def update_entitlement(
        *,
        entitlement,
        employee,
        leave_type,
        year,
        days,
        is_override=False,
        reason="",
    ):
        # -----------------------------------
        # Employee ownership validation
        # -----------------------------------

        if (
            entitlement.employee_id
            != employee.id
        ):
            raise ValueError(
                "Leave entitlement does not belong "
                "to this employee."
            )

        # -----------------------------------
        # Organization validation
        # -----------------------------------

        if (
            employee.organization_id
            != leave_type.organization_id
        ):
            raise ValueError(
                "Leave type does not belong "
                "to the employee's organization."
            )

        # -----------------------------------
        # Entitlement validation
        # -----------------------------------

        if days < 0:
            raise ValueError(
                "Entitlement days cannot be negative."
            )

        # -----------------------------------
        # Check for duplicate entitlement
        # -----------------------------------

        duplicate = (
            LeaveEntitlement.objects
            .filter(
                employee=employee,
                leave_type=leave_type,
                year=year,
            )
            .exclude(
                id=entitlement.id,
            )
            .exists()
        )

        if duplicate:
            raise ValueError(
                "An entitlement already exists "
                "for this employee, leave type, and year."
            )

        # -----------------------------------
        # Check existing balance
        # -----------------------------------

        balance = (
            LeaveBalance.objects
            .filter(
                employee=employee,
                leave_type=entitlement.leave_type,
                year=entitlement.year,
            )
            .select_for_update()
            .first()
        )

        if (
            balance is not None
            and days < balance.used_days
        ):
            raise ValueError(
                "Entitlement cannot be lower than "
                "the leave already used."
            )

        # -----------------------------------
        # Update entitlement
        # -----------------------------------

        entitlement.leave_type = leave_type
        entitlement.year = year
        entitlement.days = days
        entitlement.is_override = is_override
        entitlement.reason = reason

        entitlement.save(
            update_fields=[
                "leave_type",
                "year",
                "days",
                "is_override",
                "reason",
                "updated_at",
            ]
        )

        # -----------------------------------
        # Synchronize existing balance
        # -----------------------------------

        if balance is not None:

            balance.leave_type = leave_type
            balance.entitlement_days = days

            balance.save(
                update_fields=[
                    "leave_type",
                    "entitlement_days",
                    "updated_at",
                ]
            )

        return entitlement

    @staticmethod
    def get_employment_start_date(
        *,
        employee,
    ):
        try:
            employment = employee.employment
        except Employment.DoesNotExist:
            return None

        return employment.employment_start_date

    @staticmethod
    def calculate_prorated_days(
        *,
        annual_days,
        start_date,
        year,
    ):
        annual_days = Decimal(
            annual_days
        )

        # Employee started before this leave year.
        if start_date.year < year:
            return annual_days

        # Employee has not started yet.
        if start_date.year > year:
            return Decimal("0")

        months_remaining = (
            12 - start_date.month + 1
        )

        prorated_days = (
            annual_days
            * Decimal(months_remaining)
            / Decimal("12")
        )

        return prorated_days.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

class LeaveBalanceAdjustmentService:

    @staticmethod
    @transaction.atomic
    def create_adjustment(
        *,
        balance,
        organization,
        adjusted_by,
        amount,
        adjustment_type,
        reason,
    ):
        # -----------------------------------
        # Organization validation
        # -----------------------------------

        if (
            balance.employee.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave balance does not belong "
                "to this organization."
            )

        # -----------------------------------
        # Validate amount
        # -----------------------------------

        if amount <= 0:
            raise ValueError(
                "Adjustment amount must be greater than zero."
            )

        # -----------------------------------
        # Validate reason
        # -----------------------------------

        if not reason or not reason.strip():
            raise ValueError(
                "A reason is required for a "
                "leave balance adjustment."
            )

        # -----------------------------------
        # Validate adjustment type
        # -----------------------------------

        if adjustment_type not in (
            LeaveBalanceAdjustment
            .AdjustmentType.CREDIT,
            LeaveBalanceAdjustment
            .AdjustmentType.DEBIT,
        ):
            raise ValueError(
                "Invalid adjustment type."
            )

        # -----------------------------------
        # Lock balance
        # -----------------------------------

        balance = (
            LeaveBalance.objects
            .select_for_update()
            .get(
                id=balance.id,
            )
        )

        # -----------------------------------
        # Prevent excessive debit
        # -----------------------------------

        if (
            adjustment_type
            == LeaveBalanceAdjustment
            .AdjustmentType.DEBIT
        ):
            if (
                balance.remaining_days
                < amount
            ):
                raise ValueError(
                    "Adjustment cannot reduce "
                    "the available leave balance "
                    "below zero."
                )

        # -----------------------------------
        # Create audit record
        # -----------------------------------

        adjustment = (
            LeaveBalanceAdjustment.objects.create(
                balance=balance,
                amount=amount,
                adjustment_type=adjustment_type,
                reason=reason.strip(),
                adjusted_by=adjusted_by,
            )
        )

        return adjustment


class LeaveAccrualService:

    @staticmethod
    @transaction.atomic
    def accrue_month(
        *,
        organization,
        year,
        month,
    ):
        if month < 1 or month > 12:
            raise ValueError(
                "Month must be between 1 and 12."
            )

        balances = (
            LeaveBalance.objects
            .select_for_update()
            .filter(
                employee__organization=organization,
                year=year,
                accrual_enabled=True,
                accrual_frequency="MONTHLY",
            )
            .select_related(
                "employee",
                "leave_type",
            )
        )

        created = []

        for balance in balances:

            existing = (
                LeaveAccrual.objects
                .filter(
                    balance=balance,
                    year=year,
                    period_month=month,
                )
                .first()
            )

            if existing:
                continue

            amount = (
                LeaveAccrualService
                .calculate_period_accrual(
                    balance=balance,
                    month=month,
                )
            )

            accrual = LeaveAccrual.objects.create(
                balance=balance,
                year=year,
                period_month=month,
                amount=amount,
            )

            created.append(accrual)

        return created


    @staticmethod
    def calculate_period_accrual(
        *,
        balance,
        month,
    ):
        annual_days = balance.entitlement_days

        monthly = (
            annual_days
            / Decimal("12")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        if month < 12:
            return monthly

        accrued_before = (
            balance.accruals
            .filter(
                year=balance.year,
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )

        return (
            annual_days - accrued_before
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

class LeaveApprovalRuleService:

    @staticmethod
    @transaction.atomic
    def create_rule(
        *,
        organization,
        leave_type=None,
        approval_level,
        minimum_days=Decimal("0"),
        maximum_days=None,
    ):
        if (
            leave_type is not None
            and leave_type.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave type does not belong "
                "to this organization."
            )

        if approval_level < 1:
            raise ValueError(
                "Approval level must be at least 1."
            )

        if minimum_days < 0:
            raise ValueError(
                "Minimum days cannot be negative."
            )

        if (
            maximum_days is not None
            and maximum_days < 0
        ):
            raise ValueError(
                "Maximum days cannot be negative."
            )

        if (
            maximum_days is not None
            and minimum_days > maximum_days
        ):
            raise ValueError(
                "Maximum days cannot be less "
                "than minimum days."
            )

        duplicate = (
            LeaveApprovalRule.objects
            .filter(
                organization=organization,
                leave_type=leave_type,
                approval_level=approval_level,
            )
            .exists()
        )

        if duplicate:
            raise ValueError(
                "An approval rule already exists "
                "for this organization, leave type, "
                "and approval level."
            )

        return LeaveApprovalRule.objects.create(
            organization=organization,
            leave_type=leave_type,
            approval_level=approval_level,
            minimum_days=minimum_days,
            maximum_days=maximum_days,
        )

    @staticmethod
    @transaction.atomic
    def update_rule(
        *,
        rule,
        organization,
        leave_type=None,
        approval_level,
        minimum_days=Decimal("0"),
        maximum_days=None,
    ):
        if (
            rule.organization_id
            != organization.id
        ):
            raise ValueError(
                "Approval rule does not belong "
                "to this organization."
            )

        if (
            leave_type is not None
            and leave_type.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave type does not belong "
                "to this organization."
            )

        if approval_level < 1:
            raise ValueError(
                "Approval level must be at least 1."
            )

        if minimum_days < 0:
            raise ValueError(
                "Minimum days cannot be negative."
            )

        if (
            maximum_days is not None
            and maximum_days < 0
        ):
            raise ValueError(
                "Maximum days cannot be negative."
            )

        if (
            maximum_days is not None
            and minimum_days > maximum_days
        ):
            raise ValueError(
                "Maximum days cannot be less "
                "than minimum days."
            )

        duplicate = (
            LeaveApprovalRule.objects
            .filter(
                organization=organization,
                leave_type=leave_type,
                approval_level=approval_level,
            )
            .exclude(
                id=rule.id,
            )
            .exists()
        )

        if duplicate:
            raise ValueError(
                "Another approval rule already exists "
                "for this organization, leave type, "
                "and approval level."
            )

        rule.leave_type = leave_type
        rule.approval_level = approval_level
        rule.minimum_days = minimum_days
        rule.maximum_days = maximum_days

        rule.save(
            update_fields=[
                "leave_type",
                "approval_level",
                "minimum_days",
                "maximum_days",
                "updated_at",
            ]
        )

        return rule

    @staticmethod
    @transaction.atomic
    def activate_rule(
        *,
        rule,
        organization,
    ):
        if (
            rule.organization_id
            != organization.id
        ):
            raise ValueError(
                "Approval rule does not belong "
                "to this organization."
            )

        if rule.is_active:
            raise ValueError(
                "Approval rule is already active."
            )

        rule.is_active = True

        rule.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return rule

    @staticmethod
    @transaction.atomic
    def deactivate_rule(
        *,
        rule,
        organization,
    ):
        if (
            rule.organization_id
            != organization.id
        ):
            raise ValueError(
                "Approval rule does not belong "
                "to this organization."
            )

        if not rule.is_active:
            raise ValueError(
                "Approval rule is already inactive."
            )

        rule.is_active = False

        rule.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return rule

class LeaveApprovalService:

    @staticmethod
    def get_applicable_rules(
        *,
        organization,
        leave_type,
        requested_days,
    ):
        specific_rules = list(
            LeaveApprovalRule.objects
            .filter(
                organization=organization,
                leave_type=leave_type,
                is_active=True,
            )
            .order_by(
                "approval_level",
            )
        )

        specific_rules = [
            rule
            for rule in specific_rules
            if rule.applies_to_days(
                requested_days
            )
        ]

        if specific_rules:
            return specific_rules

        default_rules = list(
            LeaveApprovalRule.objects
            .filter(
                organization=organization,
                leave_type__isnull=True,
                is_active=True,
            )
            .order_by(
                "approval_level",
            )
        )

        return [
            rule
            for rule in default_rules
            if rule.applies_to_days(
                requested_days
            )
        ]

    @staticmethod
    def get_manager_at_level(
        *,
        employee,
        approval_level,
    ):
        if approval_level < 1:
            raise ValueError(
                "Approval level must be at least 1."
            )

        current_employee = employee
        visited_employee_ids = set()

        for _ in range(approval_level):

            if current_employee.id in visited_employee_ids:
                raise ValueError(
                    "A circular employee reporting hierarchy "
                    "was detected."
                )

            visited_employee_ids.add(
                current_employee.id
            )

            assignment = getattr(
                current_employee,
                "assignment",
                None,
            )

            if assignment is None:
                return None

            manager = assignment.manager

            if manager is None:
                return None

            if manager.id == employee.id:
                raise ValueError(
                    "An employee cannot approve their own leave."
                )

            if (
                manager.organization_id
                != employee.organization_id
            ):
                raise ValueError(
                    "Leave approver belongs "
                    "to another organization."
                )

            if not manager.is_active:
                return None

            if manager.user is None:
                return None

            if not manager.user.is_active:
                return None

            current_employee = manager

        return current_employee

    @classmethod
    def build_approval_chain(
        cls,
        *,
        leave_request,
        organization,
    ):
        if (
            leave_request.organization_id
            != organization.id
        ):
            raise ValueError(
                "Leave request does not belong "
                "to the supplied organization."
            )

        rules = cls.get_applicable_rules(
            organization=organization,
            leave_type=leave_request.leave_type,
            requested_days=leave_request.requested_days,
        )

        if not rules:
            return []

        chain = []
        expected_level = 1
        approver_ids = set()

        for rule in rules:

            if (
                rule.approval_level
                != expected_level
            ):
                raise ValueError(
                    "Leave approval levels must be sequential."
                )

            approver = cls.get_manager_at_level(
                employee=leave_request.employee,
                approval_level=rule.approval_level,
            )

            if approver is None:
                raise ValueError(
                    "No valid manager is available "
                    f"for approval level "
                    f"{rule.approval_level}."
                )

            if approver.id in approver_ids:
                raise ValueError(
                    "The same employee cannot approve "
                    "multiple levels of the same leave request."
                )

            approver_ids.add(
                approver.id
            )

            chain.append(
                {
                    "approval_level": (
                        rule.approval_level
                    ),
                    "approver_employee": approver,
                    "approver_user": approver.user,
                }
            )

            expected_level += 1

        return chain

    @classmethod
    @transaction.atomic
    def create_approval_steps(
        cls,
        *,
        leave_request,
        organization,
    ):
        existing_steps = list(
            LeaveApprovalStep.objects
            .filter(
                leave_request=leave_request,
            )
            .order_by(
                "approval_level",
            )
        )

        if existing_steps:
            return existing_steps

        chain = cls.build_approval_chain(
            leave_request=leave_request,
            organization=organization,
        )

        steps = []

        for item in chain:

            step = LeaveApprovalStep.objects.create(
                leave_request=leave_request,
                approval_level=item[
                    "approval_level"
                ],
                approver_employee=item[
                    "approver_employee"
                ],
                approver_user=item[
                    "approver_user"
                ],
                status=(
                    LeaveApprovalStep
                    .Status
                    .PENDING
                ),
            )

            steps.append(step)

        return steps

    @staticmethod
    def get_current_step(
        *,
        leave_request,
        lock=False,
    ):
        queryset = (
            LeaveApprovalStep.objects
            .filter(
                leave_request=leave_request,
                status=(
                    LeaveApprovalStep
                    .Status
                    .PENDING
                ),
            )
            .order_by(
                "approval_level",
            )
        )

        if lock:
            queryset = queryset.select_for_update()

        return queryset.first()

    @staticmethod
    def has_approval_chain(
        *,
        leave_request,
    ):
        return (
            LeaveApprovalStep.objects
            .filter(
                leave_request=leave_request,
            )
            .exists()
        )

    @staticmethod
    def can_approve(
        *,
        leave_request,
        user,
    ):
        current_step = (
            LeaveApprovalService
            .get_current_step(
                leave_request=leave_request,
            )
        )

        if current_step is None:
            return False

        return (
            current_step.approver_user_id
            == user.id
        )

    @staticmethod
    @transaction.atomic
    def approve_current_step(
        *,
        leave_request,
        user,
        comment="",
    ):
        step = (
            LeaveApprovalService
            .get_current_step(
                leave_request=leave_request,
                lock=True,
            )
        )

        if step is None:
            raise ValueError(
                "There is no pending approval step."
            )

        if (
            step.approver_user_id
            != user.id
        ):
            raise PermissionError(
                "You are not the current approver."
            )

        step.status = (
            LeaveApprovalStep
            .Status
            .APPROVED
        )

        step.comment = comment or ""
        step.acted_at = timezone.now()

        step.save(
            update_fields=[
                "status",
                "comment",
                "acted_at",
            ]
        )

        return step

    @staticmethod
    @transaction.atomic
    def reject_current_step(
        *,
        leave_request,
        user,
        comment="",
    ):
        step = (
            LeaveApprovalService
            .get_current_step(
                leave_request=leave_request,
                lock=True,
            )
        )

        if step is None:
            raise ValueError(
                "There is no pending approval step."
            )

        if (
            step.approver_user_id
            != user.id
        ):
            raise PermissionError(
                "You are not the current approver."
            )

        step.status = (
            LeaveApprovalStep
            .Status
            .REJECTED
        )

        step.comment = comment or ""
        step.acted_at = timezone.now()

        step.save(
            update_fields=[
                "status",
                "comment",
                "acted_at",
            ]
        )

        LeaveApprovalStep.objects.filter(
            leave_request=leave_request,
            status=(
                LeaveApprovalStep
                .Status
                .PENDING
            ),
        ).update(
            status=(
                LeaveApprovalStep
                .Status
                .SKIPPED
            )
        )

        return step