import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.employee.models import Employee
from apps.organization.models import Organization


class SalaryStructure(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="salary_structures")
    job_grade = models.ForeignKey("organization.JobGrade", on_delete=models.PROTECT, null=True, blank=True)
    position = models.ForeignKey("organization.Position", on_delete=models.PROTECT, null=True, blank=True)
    monthly_base = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    components = models.JSONField(default=list, blank=True)
    effective_from = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-effective_from", "id"]
        constraints = [
            models.CheckConstraint(condition=(models.Q(job_grade__isnull=False, position__isnull=True) | models.Q(job_grade__isnull=True, position__isnull=False)), name="salary_structure_one_target"),
            models.UniqueConstraint(fields=["organization", "job_grade", "effective_from"], name="salary_structure_grade_date"),
            models.UniqueConstraint(fields=["organization", "position", "effective_from"], name="salary_structure_position_date"),
        ]


class PayrollPeriod(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        PROCESSING = "PROCESSING", "Processing"
        APPROVED = "APPROVED", "Approved"
        PAID = "PAID", "Paid"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="payroll_periods")
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [models.UniqueConstraint(fields=["organization", "start_date", "end_date"], name="unique_payroll_period")]


class EmployeeCompensation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name="payroll_compensation")
    monthly_gross = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    effective_from = models.DateField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee__employee_number"]


class EmployeePayrollComponent(models.Model):
    class Kind(models.TextChoices):
        EARNING = "EARNING", "Earning"
        DEDUCTION = "DEDUCTION", "Deduction"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="payroll_components")
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    effective_from = models.DateField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee__employee_number", "kind", "name"]


class PayrollProfile(models.Model):
    class PayFrequency(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"
        BIWEEKLY = "BIWEEKLY", "Biweekly"
        WEEKLY = "WEEKLY", "Weekly"

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name="payroll_profile")
    pay_frequency = models.CharField(max_length=20, choices=PayFrequency.choices, default=PayFrequency.MONTHLY)
    tax_state = models.CharField(max_length=100, blank=True)
    tax_identification_number = models.CharField(max_length=100, blank=True)
    pension_pfa = models.CharField(max_length=200, blank=True)
    pension_pin = models.CharField(max_length=100, blank=True)
    nhf_number = models.CharField(max_length=100, blank=True)
    nhis_number = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=150, blank=True)
    bank_code = models.CharField(max_length=20, blank=True)
    account_name = models.CharField(max_length=200, blank=True)
    account_number = models.CharField(max_length=30, blank=True)
    pension_exempt = models.BooleanField(default=False)
    nhf_exempt = models.BooleanField(default=False)
    nhis_exempt = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee__employee_number"]


class PayrollInput(models.Model):
    class Kind(models.TextChoices):
        EARNING = "EARNING", "Earning"
        DEDUCTION = "DEDUCTION", "Deduction"

    class Source(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        ATTENDANCE = "ATTENDANCE", "Attendance"
        LEAVE = "LEAVE", "Leave"
        LOAN = "LOAN", "Loan"
        BONUS = "BONUS", "Bonus"
        COMMISSION = "COMMISSION", "Commission"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="payroll_inputs")
    period = models.ForeignKey("payroll.PayrollPeriod", on_delete=models.CASCADE, null=True, blank=True, related_name="inputs")
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    taxable = models.BooleanField(default=True)
    effective_from = models.DateField()
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["employee__employee_number", "kind", "name", "effective_from"]
        indexes = [models.Index(fields=["employee", "period", "effective_from"])]


class PayrollLineItem(models.Model):
    class Kind(models.TextChoices):
        EARNING = "EARNING", "Earning"
        EMPLOYEE_DEDUCTION = "EMPLOYEE_DEDUCTION", "Employee deduction"
        EMPLOYER_CONTRIBUTION = "EMPLOYER_CONTRIBUTION", "Employer contribution"

    run = models.ForeignKey("payroll.PayrollRun", on_delete=models.CASCADE, related_name="line_items")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="payroll_line_items")
    code = models.CharField(max_length=60, blank=True)
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=30, choices=Kind.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    taxable = models.BooleanField(default=False)
    source = models.CharField(max_length=30, default="CALCULATED")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["employee__employee_number", "kind", "name"]
        indexes = [models.Index(fields=["run", "employee", "kind"])]


class PayrollApproval(models.Model):
    class Action(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        PAID = "PAID", "Paid"

    run = models.ForeignKey("payroll.PayrollRun", on_delete=models.CASCADE, related_name="approvals")
    action = models.CharField(max_length=20, choices=Action.choices)
    actor = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="payroll_approvals")
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class PayrollPaymentBatch(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        PAID = "PAID", "Paid"
        PARTIAL = "PARTIAL", "Partial"
        FAILED = "FAILED", "Failed"

    run = models.OneToOneField("payroll.PayrollRun", on_delete=models.CASCADE, related_name="payment_batch")
    provider = models.CharField(max_length=100, blank=True)
    reference = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    paid_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class PayrollRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.OneToOneField(PayrollPeriod, on_delete=models.CASCADE, related_name="run")
    total_gross = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    total_deductions = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    total_net = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    processed_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)


class PayrollEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name="entries")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="payroll_entries")
    gross_pay = models.DecimalField(max_digits=14, decimal_places=2)
    deductions = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    net_pay = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["run", "employee"], name="unique_payroll_entry")]
