from rest_framework import serializers

from .models import (
    Employee,
    EmployeeIdentity,
    EmployeeContact,
    EmployeeAssignment,
    Employment,
    NextOfKin,
    EmergencyContact,
    EmployeeDocument,
)

from apps.organization.models import (
    Organization,
    Branch,
    Department,
    Team,
    Position,
    JobGrade,
)

class EmployeeIdentitySerializer(serializers.ModelSerializer):

    class Meta:
        model = EmployeeIdentity
        fields = [
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "gender",
        ]

class EmployeeContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmployeeContact
        fields = [
            "id",
            "personal_email",
            "company_email",
            "phone_number",
            "address",
        ]

class EmployeeAssignmentSerializer(serializers.ModelSerializer):

    branch_name = serializers.CharField(
        source="branch.name",
        read_only=True,
    )

    department_name = serializers.CharField(
        source="department.name",
        read_only=True,
    )

    team_name = serializers.CharField(
        source="team.name",
        read_only=True,
    )

    position_name = serializers.CharField(
        source="position.title",
        read_only=True,
    )

    job_grade_name = serializers.CharField(
        source="job_grade.name",
        read_only=True,
    )

    class Meta:
        model = EmployeeAssignment
        fields = [
            "id",
            "branch",
            "branch_name",
            "department",
            "department_name",
            "team",
            "team_name",
            "position",
            "position_name",
            "job_grade",
            "job_grade_name",
            "manager",
        ]

class EmploymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employment
        fields = [
            "id",
            "employment_type",
            "employment_status",
            "offer_date",
            "employment_start_date",
            "probation_end_date",
            "confirmation_status",
            "confirmation_date",
            "date_left",
        ]

class NextOfKinSerializer(serializers.ModelSerializer):

    class Meta:
        model = NextOfKin
        fields = [
            "id",
            "full_name",
            "relationship",
            "phone_number",
            "email",
            "address",
            "is_primary",
        ]

class EmergencyContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmergencyContact
        fields = [
            "id",
            "full_name",
            "relationship",
            "phone_number",
            "alternative_phone_number",
            "email",
            "address",
            "is_primary",
        ]


class EmployeeDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmployeeDocument
        fields = [
            "id",
            "document_type",
            "name",
            "file",
            "description",
            "issue_date",
            "expiry_date",
            "is_archived",
            "archived_at",
            "archived_by",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "is_archived",
            "archived_at",
            "archived_by",
        ]

class EmployeeSerializer(serializers.ModelSerializer):

    identity = EmployeeIdentitySerializer(
        read_only=True,
    )

    contact = EmployeeContactSerializer(
        read_only=True,
    )

    assignment = EmployeeAssignmentSerializer(
        read_only=True,
    )

    employment = EmploymentSerializer(
        read_only=True,
    )

    next_of_kin = NextOfKinSerializer(
        many=True,
        read_only=True,
    )

    emergency_contacts = EmergencyContactSerializer(
        many=True,
        read_only=True,
    )

    documents = EmployeeDocumentSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_number",
            "organization",
            "user",
            "is_active",
            "identity",
            "contact",
            "assignment",
            "employment",
            "next_of_kin",
            "emergency_contacts",
            "created_at",
            "updated_at",
            "documents",
        ]
        read_only_fields = [
            "id",
            "employee_number",
            "created_at",
            "updated_at",
        ]


class EmployeeIdentityInputSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        max_length=100,
    )

    middle_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )

    last_name = serializers.CharField(
        max_length=100,
    )

    date_of_birth = serializers.DateField(
        required=False,
        allow_null=True,
    )

    gender = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
    )

class EmployeeContactInputSerializer(serializers.Serializer):
    personal_email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    company_email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    phone_number = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
    )

    address = serializers.CharField(
        required=False,
        allow_blank=True,
    )

class EmployeeAssignmentInputSerializer(serializers.Serializer):
    branch = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

    department = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

    team = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

    position = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

    job_grade = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

    manager = serializers.UUIDField(
        required=False,
        allow_null=True,
    )

class EmploymentInputSerializer(serializers.Serializer):
    employment_type = serializers.ChoiceField(
        choices=Employment.EmploymentType.choices,
        required=False,
    )

    employment_status = serializers.ChoiceField(
        choices=Employment.EmploymentStatus.choices,
        required=False,
    )

    offer_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    employment_start_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    probation_end_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    confirmation_status = serializers.ChoiceField(
        choices=Employment.ConfirmationStatus.choices,
        required=False,
    )

    confirmation_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    date_left = serializers.DateField(
        required=False,
        allow_null=True,
    )

class EmployeeCreateSerializer(serializers.Serializer):

    identity = EmployeeIdentityInputSerializer()

    contact = EmployeeContactInputSerializer(
        required=False,
    )

    assignment = EmployeeAssignmentInputSerializer(
        required=False,
    )

    employment = EmploymentInputSerializer(
        required=False,
    )

class EmployeeUpdateSerializer(serializers.Serializer):

    identity = EmployeeIdentityInputSerializer(
        required=False,
    )

    contact = EmployeeContactInputSerializer(
        required=False,
    )

    assignment = EmployeeAssignmentInputSerializer(
        required=False,
    )

    employment = EmploymentInputSerializer(
        required=False,
    )

class EmployeeDocumentInputSerializer(
    serializers.Serializer
):

    document_type = serializers.ChoiceField(
        choices=EmployeeDocument.DocumentType.choices,
    )

    name = serializers.CharField(
        max_length=255,
    )

    file = serializers.FileField()

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    issue_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    expiry_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

class EmployeeAccountProvisionSerializer(
    serializers.Serializer
):
    role_code = serializers.CharField(
        required=False,
        default="EMPLOYEE",
    )