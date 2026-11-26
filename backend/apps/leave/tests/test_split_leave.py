from datetime import date
from decimal import Decimal
from django.test import TestCase
from apps.organization.models import Organization
from apps.employee.services import EmployeeService
from apps.leave.models import LeaveType, LeavePolicy, LeaveBalance, WorkSchedule, PublicHoliday
from apps.leave.services import LeaveRequestService


class SplitLeaveTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Leave Test")
        self.employee = EmployeeService.create_employee(organization=self.organization, first_name="Sample", last_name="Employee")
        self.leave_type = LeaveType.objects.create(organization=self.organization, code="ANNUAL", name="Annual", requires_approval=False)
        LeavePolicy.objects.create(organization=self.organization, leave_type=self.leave_type, days_per_year=40)
        WorkSchedule.objects.create(organization=self.organization, code="WEEK", name="Weekdays", is_default=True)
        self.balance = LeaveBalance.objects.create(employee=self.employee, leave_type=self.leave_type, year=2026, entitlement_days=40)

    def request(self, start, end):
        return LeaveRequestService.create_request(employee=self.employee, organization=self.organization, leave_type=self.leave_type, start_date=start, end_date=end)

    def test_split_requests_exclude_holidays_and_preserve_remaining_days(self):
        PublicHoliday.objects.create(organization=self.organization, name="Test observed holiday", date=date(2026, 10, 6))
        first = self.request(date(2026, 10, 5), date(2026, 10, 11))
        self.assertEqual(first.requested_days, Decimal("4"))
        LeaveRequestService.submit_request(leave_request=first, organization=self.organization)
        second = self.request(date(2026, 10, 12), date(2026, 10, 16))
        LeaveRequestService.submit_request(leave_request=second, organization=self.organization)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.used_days, Decimal("9"))
        self.assertEqual(self.balance.remaining_days, Decimal("31"))

    def test_cross_year_and_non_working_periods_are_rejected(self):
        with self.assertRaisesMessage(ValueError, "calendar years"):
            self.request(date(2026, 12, 31), date(2027, 1, 4))
        with self.assertRaisesMessage(ValueError, "no working days"):
            self.request(date(2026, 10, 10), date(2026, 10, 11))
