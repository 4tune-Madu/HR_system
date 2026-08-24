from django.test import TestCase

from apps.leave.models import (
    LeaveType,
    LeavePolicy,
)
from apps.leave.services import (
    LeaveTypeService,
    LeavePolicyService,
)
from apps.organization.models import Organization


class LeaveTypeServiceTests(TestCase):

    def setUp(self):

        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
        )

    def test_create_leave_type(self):

        leave_type = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        self.assertEqual(
            leave_type.organization,
            self.organization,
        )

        self.assertEqual(
            leave_type.code,
            "ANNUAL",
        )

        self.assertTrue(
            leave_type.is_paid,
        )

    def test_duplicate_leave_type_code_is_rejected(
        self,
    ):

        LeaveTypeService.create_leave_type(
            organization=self.organization,
            code="ANNUAL",
            name="Annual Leave",
        )

        with self.assertRaises(ValueError):

            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Vacation",
            )


class LeavePolicyServiceTests(TestCase):

    def setUp(self):

        self.organization = Organization.objects.create(
            name="Test Company",
            legal_name="Test Company Limited",
        )

        self.leave_type = (
            LeaveTypeService.create_leave_type(
                organization=self.organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

    def test_create_leave_policy(self):

        policy = (
            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=self.leave_type,
                days_per_year=20,
            )
        )

        self.assertEqual(
            policy.days_per_year,
            20,
        )

        self.assertFalse(
            policy.allow_carry_forward,
        )

    def test_leave_type_from_another_organization_is_rejected(
        self,
    ):

        another_organization = (
            Organization.objects.create(
                name="Another Company",
                legal_name="Another Company Limited",
            )
        )

        another_leave_type = (
            LeaveTypeService.create_leave_type(
                organization=another_organization,
                code="ANNUAL",
                name="Annual Leave",
            )
        )

        with self.assertRaises(ValueError):

            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=another_leave_type,
                days_per_year=20,
            )

    def test_minimum_request_cannot_exceed_maximum(
        self,
    ):

        with self.assertRaises(ValueError):

            LeavePolicyService.create_policy(
                organization=self.organization,
                leave_type=self.leave_type,
                days_per_year=20,
                minimum_days_per_request=10,
                maximum_days_per_request=5,
            )