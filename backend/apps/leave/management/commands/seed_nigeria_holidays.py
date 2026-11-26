from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError

from apps.leave.models import PublicHoliday
from apps.organization.models import Organization


HOLIDAYS_2026 = [
    (date(2026, 1, 1), "New Year's Day"),
    (date(2026, 3, 19), "Eid-ul-Fitr"),
    (date(2026, 3, 20), "Eid-ul-Fitr"),
    (date(2026, 4, 3), "Good Friday"),
    (date(2026, 4, 6), "Easter Monday"),
    (date(2026, 5, 1), "Workers' Day"),
    (date(2026, 5, 27), "Eid-ul-Adha"),
    (date(2026, 5, 28), "Eid-ul-Adha"),
    (date(2026, 6, 12), "Democracy Day"),
    (date(2026, 8, 25), "Eid-ul-Mawlid"),
    (date(2026, 10, 1), "Independence Day"),
    (date(2026, 12, 25), "Christmas Day"),
    (date(2026, 12, 26), "Boxing Day"),
]


class Command(BaseCommand):
    help = "Seed Nigeria's officially declared 2026 public holidays."

    def add_arguments(self, parser):
        parser.add_argument("--organization", required=True)

    def handle(self, *args, **options):
        try:
            organization = Organization.objects.get(pk=options["organization"])
        except (Organization.DoesNotExist, ValueError, ValidationError) as exc:
            raise CommandError("Organization was not found.") from exc

        for holiday_date, name in HOLIDAYS_2026:
            PublicHoliday.objects.update_or_create(
                organization=organization,
                date=holiday_date,
                defaults={"name": name, "is_active": True},
            )
        self.stdout.write(self.style.SUCCESS("Nigeria 2026 public holidays synchronized."))
