from django.db import transaction

from .models import (
    LeaveType,
    LeavePolicy,
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
        )