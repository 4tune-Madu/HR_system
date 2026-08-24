import uuid
from django.db.models import Q
from django.db import models

from apps.organization.models import Organization


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