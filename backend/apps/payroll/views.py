from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import ListCreateAPIView, ListAPIView, RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.access.permissions import HasOrganizationPermission

from .models import EmployeeCompensation, EmployeePayrollComponent, PayrollApproval, PayrollEntry, PayrollInput, PayrollLineItem, PayrollPaymentBatch, PayrollPeriod, PayrollProfile, PayrollRun
from .serializers import EmployeeCompensationSerializer, EmployeePayrollComponentSerializer, OwnPayrollEntrySerializer, PayrollInputSerializer, PayrollPeriodSerializer, PayrollProfileSerializer, PayrollRunSerializer
from .models import SalaryStructure
from .serializers import SalaryStructureSerializer
from apps.employee.models import Employee


# Nigeria 2026 PAYE monthly equivalents. PAYE is applied progressively to
# monthly taxable pay for this payroll module.
MONTHLY_PAYE_BANDS = (
    (Decimal("66666.67"), Decimal("0")),
    (Decimal("250000.00"), Decimal("0.15")),
    (Decimal("1000000.00"), Decimal("0.18")),
    (Decimal("2083333.33"), Decimal("0.21")),
    (Decimal("4166666.67"), Decimal("0.23")),
    (None, Decimal("0.25")),
)
EMPLOYEE_PENSION_RATE = Decimal("0.08")
EMPLOYER_PENSION_RATE = Decimal("0.10")


def calculate_monthly_paye(taxable_pay):
    remaining = max(Decimal(taxable_pay), Decimal("0"))
    previous_limit = Decimal("0")
    tax = Decimal("0")
    for upper_limit, rate in MONTHLY_PAYE_BANDS:
        band_amount = remaining if upper_limit is None else min(
            remaining,
            upper_limit - previous_limit,
        )
        tax += band_amount * rate
        remaining -= band_amount
        if remaining <= 0:
            break
        if upper_limit is not None:
            previous_limit = upper_limit
    return tax.quantize(Decimal("0.01"))


class CanViewPayroll(HasOrganizationPermission):
    required_permission = "payroll.view"


class CanProcessPayroll(HasOrganizationPermission):
    required_permission = "payroll.process"


class CanApprovePayroll(HasOrganizationPermission):
    required_permission = "payroll.approve"


class CanViewOwnPayroll(HasOrganizationPermission):
    required_permission = "payroll.view_own"


class SalaryStructureListView(ListCreateAPIView):
    serializer_class = SalaryStructureSerializer

    def get_permissions(self):
        return [CanViewPayroll() if self.request.method in {"GET", "HEAD", "OPTIONS"} else CanProcessPayroll()]

    def get_queryset(self):
        return SalaryStructure.objects.filter(organization=self.request.organization).select_related("job_grade", "position")

    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization)


class SalaryStructureDetailView(RetrieveUpdateAPIView):
    serializer_class = SalaryStructureSerializer
    lookup_url_kwarg = "structure_id"

    def get_permissions(self):
        return [CanViewPayroll() if self.request.method in {"GET", "HEAD", "OPTIONS"} else CanProcessPayroll()]

    def get_queryset(self):
        return SalaryStructure.objects.filter(organization=self.request.organization).select_related("job_grade", "position")


class PayrollPeriodListCreateView(ListCreateAPIView):
    serializer_class = PayrollPeriodSerializer

    def get_permissions(self):
        return [CanProcessPayroll() if self.request.method == "POST" else CanViewPayroll()]

    def get_queryset(self):
        return PayrollPeriod.objects.filter(organization=self.request.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization)


class EmployeeCompensationListCreateView(ListCreateAPIView):
    serializer_class = EmployeeCompensationSerializer

    def get_permissions(self):
        return [CanProcessPayroll() if self.request.method in {"POST", "PUT", "PATCH"} else CanViewPayroll()]

    def get_queryset(self):
        return EmployeeCompensation.objects.filter(employee__organization=self.request.organization).select_related("employee__identity")

    def perform_create(self, serializer):
        employee = self.request.organization.employees.filter(id=serializer.validated_data["employee"].id).first()
        if employee is None:
            raise ValidationError({"employee": "Employee was not found in this organization."})
        serializer.save(employee=employee)


class EmployeePayrollComponentListCreateView(ListCreateAPIView):
    serializer_class = EmployeePayrollComponentSerializer

    def get_permissions(self):
        return [CanProcessPayroll() if self.request.method == "POST" else CanViewPayroll()]

    def get_queryset(self):
        return EmployeePayrollComponent.objects.filter(employee__organization=self.request.organization).select_related("employee__identity")

    def perform_create(self, serializer):
        employee = self.request.organization.employees.filter(id=serializer.validated_data["employee"].id).first()
        if employee is None:
            raise ValidationError({"employee": "Employee was not found in this organization."})
        serializer.save(employee=employee)


class PayrollProfileListCreateView(ListCreateAPIView):
    serializer_class = PayrollProfileSerializer

    def get_permissions(self):
        return [CanProcessPayroll() if self.request.method in {"POST", "PUT", "PATCH"} else CanViewPayroll()]

    def get_queryset(self):
        return PayrollProfile.objects.filter(employee__organization=self.request.organization).select_related("employee__identity")

    def perform_create(self, serializer):
        employee = self.request.organization.employees.filter(id=serializer.validated_data["employee"].id).first()
        if employee is None:
            raise ValidationError({"employee": "Employee was not found in this organization."})
        serializer.save(employee=employee)


class PayrollInputListCreateView(ListCreateAPIView):
    serializer_class = PayrollInputSerializer

    def get_permissions(self):
        return [CanProcessPayroll() if self.request.method in {"POST", "PUT", "PATCH"} else CanViewPayroll()]

    def get_queryset(self):
        return PayrollInput.objects.filter(employee__organization=self.request.organization).select_related("employee__identity", "period")

    def perform_create(self, serializer):
        employee = self.request.organization.employees.filter(id=serializer.validated_data["employee"].id).first()
        if employee is None:
            raise ValidationError({"employee": "Employee was not found in this organization."})
        period = serializer.validated_data.get("period")
        if period is not None and period.organization_id != self.request.organization.id:
            raise ValidationError({"period": "Payroll period was not found in this organization."})
        serializer.save(employee=employee)


class PayrollRunListView(ListAPIView):
    permission_classes = [CanViewPayroll]
    serializer_class = PayrollRunSerializer

    def get_queryset(self):
        return PayrollRun.objects.filter(period__organization=self.request.organization).select_related("period").prefetch_related("entries__employee__identity", "line_items")


class PayrollRunDetailView(RetrieveAPIView):
    permission_classes = [CanViewPayroll]
    serializer_class = PayrollRunSerializer
    lookup_url_kwarg = "run_id"

    def get_queryset(self):
        return PayrollRun.objects.filter(period__organization=self.request.organization).select_related("period").prefetch_related("entries__employee__identity", "line_items")


class OwnPayrollEntryListView(ListAPIView):
    permission_classes = [CanViewOwnPayroll]
    serializer_class = OwnPayrollEntrySerializer

    def get_queryset(self):
        employee = getattr(self.request.user, "employee_profile", None)
        if employee is None:
            return PayrollEntry.objects.none()
        return PayrollEntry.objects.filter(
            employee=employee,
            run__period__organization=self.request.organization,
            run__period__status__in=[PayrollPeriod.Status.APPROVED, PayrollPeriod.Status.PAID],
        ).select_related("run__period").order_by("-run__period__start_date")


class PayrollProcessView(APIView):
    permission_classes = [CanProcessPayroll]

    @transaction.atomic
    @extend_schema(request=None, responses=PayrollRunSerializer)
    def post(self, request, organization_id, period_id):
        period = PayrollPeriod.objects.select_for_update().filter(id=period_id, organization=request.organization).first()
        if period is None:
            raise NotFound("Payroll period was not found in this organization.")
        if period.status != PayrollPeriod.Status.OPEN:
            raise ValidationError("Only open payroll periods can be processed.")
        compensations = EmployeeCompensation.objects.filter(
            employee__organization=request.organization,
            employee__is_active=True,
            is_active=True,
            effective_from__lte=period.end_date,
        )
        overrides = {item.employee_id: item for item in compensations}
        structures = list(SalaryStructure.objects.filter(organization=request.organization, is_active=True, effective_from__lte=period.end_date))
        candidates = []
        for employee in Employee.objects.filter(organization=request.organization, is_active=True).select_related("assignment__position"):
            assignment = getattr(employee, "assignment", None)
            override = overrides.get(employee.id)
            position_id = assignment.position_id if assignment else None
            grade_id = assignment.job_grade_id if assignment else None
            if not grade_id and assignment and assignment.position:
                grade_id = assignment.position.job_grade_id
            structure = next((item for item in structures if position_id and item.position_id == position_id), None)
            if structure is None:
                structure = next((item for item in structures if grade_id and item.job_grade_id == grade_id), None)
            if override or structure:
                candidates.append((employee, override, structure))
        if not candidates:
            raise ValidationError("No active employee compensation records or salary structures are effective for this period.")
        run = PayrollRun.objects.create(period=period)
        entries = []
        line_items = []
        for employee, override, structure in candidates:
            components = EmployeePayrollComponent.objects.filter(
                employee=employee,
                is_active=True,
                effective_from__lte=period.end_date,
            )
            earnings = sum((component.amount for component in components if component.kind == EmployeePayrollComponent.Kind.EARNING), 0)
            deductions = sum((component.amount for component in components if component.kind == EmployeePayrollComponent.Kind.DEDUCTION), 0)
            base = override.monthly_gross if override else structure.monthly_base
            structure_components = [] if override else structure.components
            earnings += sum((Decimal(item["amount"]) for item in structure_components if item["kind"] == "EARNING"), Decimal("0"))
            deductions += sum((Decimal(item["amount"]) for item in structure_components if item["kind"] == "DEDUCTION"), Decimal("0"))
            gross_pay = base + earnings
            employee_pension = (gross_pay * EMPLOYEE_PENSION_RATE).quantize(Decimal("0.01"))
            paye = calculate_monthly_paye(gross_pay - employee_pension)
            deductions += employee_pension + paye
            if deductions > gross_pay:
                raise ValidationError(f"Deductions exceed gross pay for {employee.employee_number}.")
            source = "Employee compensation" if override else f"Salary structure {structure.id} effective {structure.effective_from}"
            detail = [
                f"{source}; base {base}",
                f"PAYE (Nigeria 2026 progressive bands): {paye}",
                f"Employee pension (8%): {employee_pension}",
                f"Employer pension (10%): {(gross_pay * EMPLOYER_PENSION_RATE).quantize(Decimal('0.01'))}",
            ]
            line_items.append(PayrollLineItem(run=run, employee=employee, code="BASE", name="Base salary", kind=PayrollLineItem.Kind.EARNING, amount=base, taxable=True, source="COMPENSATION"))
            detail.extend(f"{item['name']} ({item['kind']}): {item['amount']}" for item in structure_components)
            line_items.extend(
                PayrollLineItem(
                    run=run,
                    employee=employee,
                    name=item["name"],
                    kind=PayrollLineItem.Kind.EARNING if item["kind"] == "EARNING" else PayrollLineItem.Kind.EMPLOYEE_DEDUCTION,
                    amount=Decimal(item["amount"]),
                    taxable=item["kind"] == "EARNING",
                    source="SALARY_STRUCTURE",
                )
                for item in structure_components
            )
            detail.extend(f"{item.name} ({item.kind}): {item.amount}" for item in components)
            line_items.extend(
                PayrollLineItem(
                    run=run,
                    employee=employee,
                    name=item.name,
                    kind=PayrollLineItem.Kind.EARNING if item.kind == EmployeePayrollComponent.Kind.EARNING else PayrollLineItem.Kind.EMPLOYEE_DEDUCTION,
                    amount=item.amount,
                    taxable=item.kind == EmployeePayrollComponent.Kind.EARNING,
                    source="EMPLOYEE_COMPONENT",
                )
                for item in components
            )
            line_items.extend([
                PayrollLineItem(
                    run=run,
                    employee=employee,
                    code="PAYE",
                    name="PAYE tax",
                    kind=PayrollLineItem.Kind.EMPLOYEE_DEDUCTION,
                    amount=paye,
                    source="NIGERIA_TAX_2026",
                ),
                PayrollLineItem(
                    run=run,
                    employee=employee,
                    code="PENSION_EMPLOYEE",
                    name="Employee pension",
                    kind=PayrollLineItem.Kind.EMPLOYEE_DEDUCTION,
                    amount=employee_pension,
                    source="PENCOM",
                ),
                PayrollLineItem(
                    run=run,
                    employee=employee,
                    code="PENSION_EMPLOYER",
                    name="Employer pension",
                    kind=PayrollLineItem.Kind.EMPLOYER_CONTRIBUTION,
                    amount=(gross_pay * EMPLOYER_PENSION_RATE).quantize(Decimal("0.01")),
                    source="PENCOM",
                ),
            ])
            entries.append(PayrollEntry(run=run, employee=employee, gross_pay=gross_pay, deductions=deductions, net_pay=gross_pay - deductions, notes="\n".join(detail)))
        PayrollEntry.objects.bulk_create(entries)
        PayrollLineItem.objects.bulk_create(line_items)
        run.total_gross = sum((item.gross_pay for item in entries), 0)
        run.total_deductions = sum((item.deductions for item in entries), 0)
        run.total_net = run.total_gross - run.total_deductions
        run.save(update_fields=["total_gross", "total_deductions", "total_net"])
        period.status = PayrollPeriod.Status.PROCESSING
        period.save(update_fields=["status", "updated_at"])
        PayrollApproval.objects.create(run=run, action=PayrollApproval.Action.SUBMITTED, actor=request.user)
        return Response(PayrollRunSerializer(run).data, status=status.HTTP_201_CREATED)


class PayrollApproveView(APIView):
    permission_classes = [CanApprovePayroll]

    @extend_schema(request=None, responses=PayrollRunSerializer)
    def post(self, request, organization_id, run_id):
        run = PayrollRun.objects.filter(id=run_id, period__organization=request.organization).select_related("period").first()
        if run is None:
            raise NotFound("Payroll run was not found in this organization.")
        if run.period.status != PayrollPeriod.Status.PROCESSING:
            raise ValidationError("Only processed payroll runs can be approved.")
        run.period.status = PayrollPeriod.Status.APPROVED
        run.period.save(update_fields=["status", "updated_at"])
        run.approved_at = timezone.now()
        run.save(update_fields=["approved_at"])
        PayrollApproval.objects.create(run=run, action=PayrollApproval.Action.APPROVED, actor=request.user)
        return Response(PayrollRunSerializer(run).data)


class PayrollMarkPaidView(APIView):
    permission_classes = [CanApprovePayroll]

    @extend_schema(request=None, responses=PayrollRunSerializer)
    def post(self, request, organization_id, run_id):
        run = PayrollRun.objects.filter(
            id=run_id,
            period__organization=request.organization,
        ).select_related("period").first()
        if run is None:
            raise NotFound("Payroll run was not found in this organization.")
        if run.period.status != PayrollPeriod.Status.APPROVED:
            raise ValidationError("Only approved payroll runs can be marked as paid.")
        run.period.status = PayrollPeriod.Status.PAID
        run.period.save(update_fields=["status", "updated_at"])
        PayrollApproval.objects.create(run=run, action=PayrollApproval.Action.PAID, actor=request.user)
        PayrollPaymentBatch.objects.update_or_create(
            run=run,
            defaults={
                "status": PayrollPaymentBatch.Status.PAID,
                "total_amount": run.total_net,
                "paid_at": timezone.now(),
            },
        )
        return Response(PayrollRunSerializer(run).data)
