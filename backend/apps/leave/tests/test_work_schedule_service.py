from datetime import date, time

from django.test import TestCase

from apps.organization.models import Organization
from apps.employee.services import EmployeeService

from apps.leave.models import (
    WorkSchedule,
    WorkScheduleDay,
    EmployeeWorkSchedule,
)

from apps.leave.services import (
    WorkScheduleService,
)


class WorkScheduleServiceTests(TestCase):

    def setUp(self):

        self.organization = (
            Organization.objects.create(
                name="Test Company",
                legal_name="Test Company Ltd",
            )
        )

        self.employee = (
            EmployeeService.create_employee(
                organization=self.organization,
                first_name="John",
                last_name="Doe",
                company_email="john@test.com",
            )
        )

        self.schedule = (
            WorkSchedule.objects.create(
                organization=self.organization,
                code="STD",
                name="Standard",
            )
        )

        WorkScheduleDay.objects.create(
            work_schedule=self.schedule,
            day_of_week=0,
            start_time=time(8, 0),
            end_time=time(17, 0),
            grace_period_minutes=15,
        )

        EmployeeWorkSchedule.objects.create(
            employee=self.employee,
            work_schedule=self.schedule,
            effective_from=date(
                2026,
                1,
                1,
            ),
        )

    def test_get_schedule_day(self):

        schedule_day = (
            WorkScheduleService
            .get_schedule_day(
                employee=self.employee,
                attendance_date=date(
                    2026,
                    9,
                    21,
                ),
            )
        )

        self.assertIsNotNone(
            schedule_day,
        )

        self.assertEqual(
            schedule_day.start_time.hour,
            8,
        )

        self.assertEqual(
            schedule_day.end_time.hour,
            17,
        )
