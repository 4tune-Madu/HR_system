from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.organization.models import Organization, Branch, Department, Team, JobGrade, Position
from apps.leave.models import LeaveType


DEPARTMENTS = [
    ("EXEC", "Executive Office"), ("HR", "Human Resources"),
    ("FIN", "Finance and Accounts"), ("ENG", "Engineering"),
    ("IT", "IT and Infrastructure"), ("PROD", "Product and Design"),
    ("OPS", "Operations"), ("SALES", "Sales and Business Development"),
    ("MKT", "Marketing and Communications"), ("CS", "Customer Success"),
    ("ADMIN", "Administration"),
]
GRADES = ["Intern", "Junior", "Senior", "Lead/Executive/Supervisor", "Manager", "General Manager", "Director"]
POSITIONS = [
    ("CEO", "Chief Executive Officer", "EXEC", 6),
    ("COO", "Chief Operating Officer", "EXEC", 6),
    ("HR-MGR", "HR Manager", "HR", 6), ("HR-OFF", "HR Officer", "HR", 3),
    ("HR-ASST", "HR Assistant", "HR", 2),
    ("FIN-MGR", "Finance Manager", "FIN", 6), ("ACCOUNTANT", "Accountant", "FIN", 3),
    ("PAYROLL", "Payroll Officer", "FIN", 3),
    ("ENG-MGR", "Engineering Manager", "ENG", 6),
    ("TECH-LEAD", "Technical Lead", "ENG", 5),
    ("SR-SWE", "Senior Software Engineer", "ENG", 4),
    ("SWE", "Software Engineer", "ENG", 3),
    ("FRONTEND", "Frontend Developer", "ENG", 3),
    ("BACKEND", "Backend Developer", "ENG", 3),
    ("QA", "QA Engineer", "ENG", 3),
    ("DEVOPS", "DevOps Engineer", "IT", 4),
    ("SYSADMIN", "Systems Administrator", "IT", 3),
    ("IT-SUPPORT", "IT Support Officer", "IT", 2),
    ("PROD-MGR", "Product Manager", "PROD", 6),
    ("DESIGNER", "UI/UX Designer", "PROD", 3),
    ("DATA", "Data Analyst", "PROD", 3),
    ("OPS-MGR", "Operations Manager", "OPS", 6),
    ("PROJECT-MGR", "Project Manager", "OPS", 6),
    ("SALES-MGR", "Sales Manager", "SALES", 6),
    ("BIZDEV", "Business Development Executive", "SALES", 3),
    ("MKT-OFF", "Marketing Officer", "MKT", 3),
    ("CONTENT", "Content and Communications Specialist", "MKT", 3),
    ("CS-MGR", "Customer Success Manager", "CS", 6),
    ("CS-OFF", "Customer Support Officer", "CS", 2),
    ("ADMIN-OFF", "Administrative Officer", "ADMIN", 3),
    ("OFFICE-ASST", "Office Assistant", "ADMIN", 2),
    ("INTERN", "Graduate Intern", "HR", 1),
]


class Command(BaseCommand):
    help = "Add editable starter dropdown options to one local organization without replacing existing records."

    def add_arguments(self, parser):
        parser.add_argument("--organization", required=True, help="Organization UUID")

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            organization = Organization.objects.get(pk=options["organization"])
        except (Organization.DoesNotExist, ValueError, ValidationError):
            raise CommandError("Organization was not found. Supply its UUID.")
        counts = {}

        def ensure(model, lookup, defaults):
            obj, created = model.objects.get_or_create(**lookup, defaults=defaults)
            counts[model.__name__] = counts.get(model.__name__, 0) + int(created)
            return obj

        for code, name in [
            ("HQ", "Head Office"), ("LAG", "Lagos Branch"), ("ABJ", "Abuja Branch"),
            ("PHC", "Port Harcourt Branch"), ("REMOTE", "Remote / Work from Home"),
        ]:
            ensure(Branch, {"organization": organization, "code": code}, {"name": name})

        departments = {
            code: ensure(Department, {"organization": organization, "code": code},
                         {"name": name, "description": "Editable local starter option."})
            for code, name in DEPARTMENTS
        }
        grades = {
            level: self.ensure_grade(organization, level, name, counts)
            for level, name in enumerate(GRADES, start=1)
        }
        JobGrade.objects.filter(organization=organization, code__startswith="G").exclude(
            code__in=[f"G{level:02}" for level in grades]
        ).update(is_active=False)
        for department_code, code, name in [
            ("HR", "PEOPLE", "People Operations"), ("FIN", "ACCOUNTS", "Accounts and Payroll"),
            ("ENG", "WEB", "Web Development"), ("ENG", "PLATFORM", "Platform Engineering"),
            ("ENG", "QUALITY", "Quality Assurance"), ("IT", "INFRA", "Infrastructure and Support"),
            ("PROD", "PRODUCT", "Product Management"), ("PROD", "DESIGN", "Design and Research"),
            ("OPS", "DELIVERY", "Project Delivery"), ("SALES", "GROWTH", "Business Development"),
            ("MKT", "COMM", "Marketing and Communications"), ("CS", "SUPPORT", "Customer Support"),
            ("ADMIN", "OFFICE", "Office Administration"),
        ]:
            ensure(Team, {"department": departments[department_code], "code": code}, {"name": name})
        for code, title, department, grade in POSITIONS:
            ensure(Position, {"organization": organization, "code": code},
                   {"title": title, "department": departments[department], "job_grade": grades[grade]})
        for code, name, paid in [
            ("ANNUAL", "Annual Leave", True), ("SICK", "Sick Leave", True),
            ("MATERNITY", "Maternity Leave", True), ("PATERNITY", "Paternity Leave", True),
            ("COMPASSIONATE", "Compassionate Leave", True), ("STUDY", "Study Leave", True),
            ("UNPAID", "Unpaid Leave", False),
        ]:
            ensure(LeaveType, {"organization": organization, "code": code},
                   {"name": name, "is_paid": paid, "description": "Local starter type; configure company policy before use."})
        self.stdout.write(self.style.SUCCESS(f"Starter options added for {organization.name}. Existing records preserved."))
        for name, count in counts.items():
            self.stdout.write(f"{name}: {count} created")

    def ensure_grade(self, organization, level, name, counts):
        grade, created = JobGrade.objects.get_or_create(
            organization=organization,
            code=f"G{level:02}",
            defaults={"name": name, "level": level, "description": "Editable local starter option."},
        )
        if not created and (grade.name != name or grade.level != level):
            grade.name = name
            grade.level = level
            grade.save(update_fields=["name", "level", "updated_at"])
        counts[JobGrade.__name__] = counts.get(JobGrade.__name__, 0) + int(created)
        return grade
