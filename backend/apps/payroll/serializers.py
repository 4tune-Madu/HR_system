from rest_framework import serializers

from .models import EmployeeCompensation, EmployeePayrollComponent, PayrollEntry, PayrollInput, PayrollLineItem, PayrollPeriod, PayrollProfile, PayrollRun
from .models import SalaryStructure


class StructureComponentSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    kind = serializers.ChoiceField(choices=EmployeePayrollComponent.Kind.choices)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)


class SalaryStructureSerializer(serializers.ModelSerializer):
    components = StructureComponentSerializer(many=True, required=False)
    job_grade_name = serializers.CharField(source="job_grade.name", read_only=True)
    position_name = serializers.CharField(source="position.title", read_only=True)

    class Meta:
        model = SalaryStructure
        fields = ["id", "job_grade", "job_grade_name", "position", "position_name", "monthly_base", "components", "effective_from", "is_active"]
        validators = []

    def validate(self, attrs):
        grade = attrs.get("job_grade", getattr(self.instance, "job_grade", None))
        position = attrs.get("position", getattr(self.instance, "position", None))
        organization = self.context["request"].organization
        if bool(grade) == bool(position):
            raise serializers.ValidationError("Choose exactly one job grade or position.")
        if (grade or position).organization_id != organization.id:
            raise serializers.ValidationError("The grade or position must belong to this organization.")
        date = attrs.get("effective_from", getattr(self.instance, "effective_from", None))
        duplicates = SalaryStructure.objects.filter(organization=organization, job_grade=grade, position=position, effective_from=date)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("A structure already exists for this assignment and effective date. Edit it instead.")
        if "components" in attrs:
            attrs["components"] = [{**item, "amount": str(item["amount"])} for item in attrs["components"]]
        return attrs


class PayrollPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollPeriod
        fields = ["id", "name", "start_date", "end_date", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def validate(self, attrs):
        if attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError("end_date cannot be earlier than start_date.")
        return attrs


class EmployeeCompensationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.identity.full_name", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)

    class Meta:
        model = EmployeeCompensation
        fields = ["id", "employee", "employee_name", "employee_number", "monthly_gross", "effective_from", "is_active", "updated_at"]
        read_only_fields = ["id", "employee_name", "employee_number", "updated_at"]


class EmployeePayrollComponentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.identity.full_name", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)

    class Meta:
        model = EmployeePayrollComponent
        fields = ["id", "employee", "employee_name", "employee_number", "name", "kind", "amount", "effective_from", "is_active", "updated_at"]
        read_only_fields = ["id", "employee_name", "employee_number", "updated_at"]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Component name is required.")
        return value.strip()


class PayrollProfileSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.identity.full_name", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)

    class Meta:
        model = PayrollProfile
        fields = [
            "id", "employee", "employee_name", "employee_number", "pay_frequency", "tax_state",
            "tax_identification_number", "pension_pfa", "pension_pin", "nhf_number", "nhis_number",
            "bank_name", "bank_code", "account_name", "account_number", "pension_exempt", "nhf_exempt",
            "nhis_exempt", "is_active", "updated_at",
        ]
        read_only_fields = ["id", "employee_name", "employee_number", "updated_at"]


class PayrollInputSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.identity.full_name", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)

    class Meta:
        model = PayrollInput
        fields = [
            "id", "employee", "employee_name", "employee_number", "period", "name", "kind", "source",
            "amount", "taxable", "effective_from", "notes", "is_active", "created_at",
        ]
        read_only_fields = ["id", "employee_name", "employee_number", "created_at"]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Payroll input name is required.")
        return value.strip()


class PayrollEntrySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.identity.full_name", read_only=True)
    employee_number = serializers.CharField(source="employee.employee_number", read_only=True)

    class Meta:
        model = PayrollEntry
        fields = ["id", "employee", "employee_name", "employee_number", "gross_pay", "deductions", "net_pay", "notes"]


class PayrollLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollLineItem
        fields = ["id", "employee", "code", "name", "kind", "amount", "taxable", "source", "metadata"]


class PayrollRunSerializer(serializers.ModelSerializer):
    period_name = serializers.CharField(source="period.name", read_only=True)
    period_status = serializers.CharField(source="period.status", read_only=True)
    entries = PayrollEntrySerializer(many=True, read_only=True)
    line_items = PayrollLineItemSerializer(many=True, read_only=True)

    class Meta:
        model = PayrollRun
        fields = ["id", "period", "period_name", "period_status", "total_gross", "total_deductions", "total_net", "processed_at", "approved_at", "entries", "line_items"]


class OwnPayrollEntrySerializer(serializers.ModelSerializer):
    period_name = serializers.CharField(source="run.period.name", read_only=True)
    period_start = serializers.DateField(source="run.period.start_date", read_only=True)
    period_end = serializers.DateField(source="run.period.end_date", read_only=True)

    class Meta:
        model = PayrollEntry
        fields = ["id", "period_name", "period_start", "period_end", "gross_pay", "deductions", "net_pay", "notes"]
