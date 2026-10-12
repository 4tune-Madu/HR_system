from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import (
    Employee,
    Employment,
)

from .serializers import (
    EmployeeSerializer,
    EmployeeCreateSerializer,
)

from .services import EmployeeService

from apps.organization.models import (
    Organization,
    Branch,
    Department,
    Team,
    Position,
    JobGrade,
)


from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.access.permissions import (
    CanViewEmployees,
    CanCreateEmployees,
    CanUpdateEmployees,
    CanDeactivateEmployees,
    CanUploadEmployeeDocuments,
    CanViewEmployeeDocuments,
    CanArchiveEmployeeDocuments,
    CanRestoreEmployeeDocuments,
    CanProvisionEmployeeAccounts,
    CanInviteEmployeeAccounts,
    CanActivateEmployees,
)

from apps.employee.models import (
    Employee,
    Employment,
    Branch,
    Department,
    Team,
    Position,
    JobGrade,
    EmployeeDocument,
)

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
)

from apps.employee.serializers import (
    EmployeeSerializer,
    EmployeeCreateSerializer,
    EmployeeUpdateSerializer,
    EmployeeDocumentSerializer,
    EmployeeDocumentInputSerializer,
    EmployeeAccountProvisionSerializer,
)

from apps.employee.services import EmployeeService

from rest_framework.parsers import (
    MultiPartParser,
    FormParser,
)

from apps.authentication.services import (
    AccountService,
)
from .services import EmployeeDocumentService

class EmployeeListView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewEmployees()
            ]

        if self.request.method == "POST":
            return [
                CanCreateEmployees()
            ]

        return []


    @extend_schema(
        operation_id="employee_list",
        summary="List employees",
        description=(
            "Return all employees belonging to the specified "
            "organization."
        ),
        responses=EmployeeSerializer(many=True),
        tags=["Employees"],
    )
    def get(self, request, organization_id):

        employees = EmployeeService.list_employees(
            organization=request.organization
        )

        serializer = EmployeeSerializer(
            employees,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="employee_create",
        summary="Create employee",
        description=(
            "Create a new employee and their related "
            "employee records."
        ),
        request=EmployeeCreateSerializer,
        responses=EmployeeSerializer,
        tags=["Employees"],
    )
    def post(self, request, organization_id):

        # -----------------------------------
        # Validate request data
        # -----------------------------------

        serializer = EmployeeCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        # -----------------------------------
        # Extract nested data
        # -----------------------------------

        identity_data = data["identity"]

        contact_data = data.get(
            "contact",
            {},
        )

        assignment_data = data.get(
            "assignment",
            {},
        )

        employment_data = data.get(
            "employment",
            {},
        )

        # -----------------------------------
        # Resolve assignment objects
        # -----------------------------------

        branch = None
        department = None
        team = None
        position = None
        job_grade = None
        manager = None

        if assignment_data.get("branch"):
            branch = get_object_or_404(
                Branch,
                id=assignment_data["branch"],
                organization=request.organization,
            )

        if assignment_data.get("department"):
            department = get_object_or_404(
                Department,
                id=assignment_data["department"],
                organization=request.organization,
            )

        if assignment_data.get("team"):
            team = get_object_or_404(
                Team,
                id=assignment_data["team"],
                organization=request.organization,
            )

        if assignment_data.get("position"):
            position = get_object_or_404(
                Position,
                id=assignment_data["position"],
                organization=request.organization,
            )

        if assignment_data.get("job_grade"):
            job_grade = get_object_or_404(
                JobGrade,
                id=assignment_data["job_grade"],
                organization=request.organization,
            )

        if assignment_data.get("manager"):
            manager = get_object_or_404(
                Employee,
                id=assignment_data["manager"],
                organization=request.organization,
            )

        # -----------------------------------
        # Create employee through service
        # -----------------------------------

        try:

            employee = EmployeeService.create_employee(

                # IMPORTANT:
                # Organization comes from the
                # authenticated user's RBAC context.

                organization=request.organization,

                # -----------------------------------
                # Identity
                # -----------------------------------

                first_name=identity_data["first_name"],

                middle_name=identity_data.get(
                    "middle_name",
                    "",
                ),

                last_name=identity_data["last_name"],

                date_of_birth=identity_data.get(
                    "date_of_birth"
                ),

                gender=identity_data.get(
                    "gender",
                    "",
                ),

                # -----------------------------------
                # Contact
                # -----------------------------------

                personal_email=contact_data.get(
                    "personal_email",
                    "",
                ),

                company_email=contact_data.get(
                    "company_email",
                    "",
                ),

                phone_number=contact_data.get(
                    "phone_number",
                    "",
                ),

                address=contact_data.get(
                    "address",
                    "",
                ),

                # -----------------------------------
                # Assignment
                # -----------------------------------

                branch=branch,

                department=department,

                team=team,

                position=position,

                job_grade=job_grade,

                manager=manager,

                # -----------------------------------
                # Employment
                # -----------------------------------

                employment_type=employment_data.get(
                    "employment_type",
                    Employment.EmploymentType.PERMANENT,
                ),

                employment_status=employment_data.get(
                    "employment_status",
                    Employment.EmploymentStatus.PROBATION,
                ),

                offer_date=employment_data.get(
                    "offer_date"
                ),

                employment_start_date=employment_data.get(
                    "employment_start_date"
                ),

                probation_end_date=employment_data.get(
                    "probation_end_date"
                ),

                confirmation_status=employment_data.get(
                    "confirmation_status",
                    Employment.ConfirmationStatus.PENDING,
                ),

                confirmation_date=employment_data.get(
                    "confirmation_date"
                ),

                date_left=employment_data.get(
                    "date_left"
                ),
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------------
        # Return created employee
        # -----------------------------------

        response_serializer = EmployeeSerializer(
            employee
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

class EmployeeDetailView(APIView):

    permission_classes = [
        CanViewEmployees,
    ]

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewEmployees()
            ]

        if self.request.method == "PATCH":
            return [
                CanUpdateEmployees()
            ]

        if self.request.method == "POST":
            return [
                CanDeactivateEmployees()
            ]

        return [
            CanViewEmployees()
        ]

    serializer_class = EmployeeSerializer
    @extend_schema(
        operation_id="employee_detail",
        summary="Get employee",
        description="Retrieve a single employee within an organization.",
        responses=EmployeeSerializer,
        tags=["Employees"],
    )
    def get(
        self,
        request,
        organization_id,
        employee_id,
    ):

        try:

            employee = EmployeeService.get_employee(
                employee_id=employee_id,
                organization=request.organization,
            )

        except Employee.DoesNotExist:

            return Response(
                {
                    "detail": "Employee not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EmployeeSerializer(
            employee
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="employee_update",
        summary="Update employee",
        description="Update an employee and their related employee information.",
        request=EmployeeCreateSerializer,
        responses=EmployeeSerializer,
        tags=["Employees"],
    )
    def patch(
        self,
        request,
        organization_id,
        employee_id,
    ):

        # -----------------------------------------
        # Get employee
        # -----------------------------------------

        try:

            employee = EmployeeService.get_employee(
                employee_id=employee_id,
                organization=request.organization,
            )

        except Employee.DoesNotExist:

            return Response(
                {
                    "detail": "Employee not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -----------------------------------------
        # Validate request
        # -----------------------------------------

        serializer = EmployeeUpdateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        # -----------------------------------------
        # Extract sections
        # -----------------------------------------

        identity_data = data.get(
            "identity",
        )

        contact_data = data.get(
            "contact",
        )

        assignment_data = data.get(
            "assignment",
        )

        employment_data = data.get(
            "employment",
        )

        # -----------------------------------------
        # Resolve assignment objects
        # -----------------------------------------

        if assignment_data is not None:

            assignment_data = assignment_data.copy()

            if assignment_data.get("branch"):

                assignment_data["branch"] = (
                    get_object_or_404(
                        Branch,
                        id=assignment_data["branch"],
                        organization=request.organization,
                    )
                )

            if assignment_data.get("department"):

                assignment_data["department"] = (
                    get_object_or_404(
                        Department,
                        id=assignment_data["department"],
                        organization=request.organization,
                    )
                )

            if assignment_data.get("team"):

                assignment_data["team"] = (
                    get_object_or_404(
                        Team,
                        id=assignment_data["team"],
                        department__organization=request.organization,
                    )
                )

            if assignment_data.get("position"):

                assignment_data["position"] = (
                    get_object_or_404(
                        Position,
                        id=assignment_data["position"],
                        organization=request.organization,
                    )
                )

            if assignment_data.get("job_grade"):

                assignment_data["job_grade"] = (
                    get_object_or_404(
                        JobGrade,
                        id=assignment_data["job_grade"],
                        organization=request.organization,
                    )
                )

            if assignment_data.get("manager"):

                assignment_data["manager"] = (
                    get_object_or_404(
                        Employee,
                        id=assignment_data["manager"],
                        organization=request.organization,
                    )
                )

        # -----------------------------------------
        # Update employee
        # -----------------------------------------

        try:

            employee = EmployeeService.update_employee(
                employee=employee,
                identity_data=identity_data,
                contact_data=contact_data,
                assignment_data=assignment_data,
                employment_data=employment_data,
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------------------
        # Return updated employee
        # -----------------------------------------

        response_serializer = EmployeeSerializer(
            employee,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="employee_deactivate",
        summary="Deactivate employee",
        description=(
            "Deactivate an employee. "
            "The employee is not deleted and can no longer be treated as active."
        ),
        responses=EmployeeSerializer,
        tags=["Employees"],
    )
    def post(
        self,
        request,
        organization_id,
        employee_id,
    ):

        try:

            employee = EmployeeService.get_employee(
                employee_id=employee_id,
                organization=request.organization,
            )

        except Employee.DoesNotExist:

            return Response(
                {
                    "detail": "Employee not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not employee.is_active:

            return Response(
                {
                    "detail": "Employee is already inactive."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        employee = EmployeeService.deactivate_employee(
            employee=employee,
        )

        serializer = EmployeeSerializer(
            employee
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class EmployeeDocumentListView(APIView):

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewEmployeeDocuments()
            ]

        if self.request.method == "POST":
            return [
                CanUploadEmployeeDocuments()
            ]

        return []

    @extend_schema(
        operation_id="employee_document_list",
        summary="List employee documents",
        description=(
            "Return all active documents belonging to the specified employee."
        ),
        responses=EmployeeDocumentSerializer(many=True),
        tags=["Employee Documents"],
    )
    def get(
        self,
        request,
        organization_id,
        employee_id,
    ):

        try:
            employee = (
                EmployeeService
                .get_employee_for_organization(
                    employee_id=employee_id,
                    organization=request.organization,
                )
            )

        except Employee.DoesNotExist:
            return Response(
                {
                    "detail": "Employee not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        documents = (
            EmployeeDocumentService
            .list_documents(
                employee=employee,
            )
        )

        serializer = EmployeeDocumentSerializer(
            documents,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


    @extend_schema(
        operation_id="employee_document_upload",
        summary="Upload employee document",
        description=(
            "Upload a document and associate it with the specified employee."
        ),
        request=EmployeeDocumentSerializer,
        responses=EmployeeDocumentSerializer,
        tags=["Employee Documents"],
    )
    def post(
        self,
        request,
        organization_id,
        employee_id,
    ):

        try:
            employee = (
                EmployeeService
                .get_employee_for_organization(
                    employee_id=employee_id,
                    organization=request.organization,
                )
            )

        except Employee.DoesNotExist:
            return Response(
                {
                    "detail": "Employee not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = (
            EmployeeDocumentInputSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        document = (
            EmployeeDocumentService
            .create_document(
                employee=employee,
                document_type=data[
                    "document_type"
                ],
                name=data["name"],
                file=data["file"],
                description=data.get(
                    "description",
                    "",
                ),
                issue_date=data.get(
                    "issue_date"
                ),
                expiry_date=data.get(
                    "expiry_date"
                ),
            )
        )

        response_serializer = (
            EmployeeDocumentSerializer(
                document
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

class EmployeeDocumentDetailView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewEmployeeDocuments()
            ]

        if self.request.method == "DELETE":
            return [
                CanArchiveEmployeeDocuments()
            ]

        return []

    @extend_schema(
        operation_id="employee_document_detail",
        summary="Get employee document",
        description=(
            "Retrieve a single active document belonging to an employee."
        ),
        responses=EmployeeDocumentSerializer,
        tags=["Employee Documents"],
    )
    def get(
        self,
        request,
        organization_id,
        employee_id,
        document_id,
    ):

        try:
            employee = (
                EmployeeService
                .get_employee_for_organization(
                    employee_id=employee_id,
                    organization=request.organization,
                )
            )

        except Employee.DoesNotExist:
            return Response(
                {
                    "detail": "Employee not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            document = (
                EmployeeDocumentService
                .get_document(
                    employee=employee,
                    document_id=document_id,
                )
            )

        except EmployeeDocument.DoesNotExist:
            return Response(
                {
                    "detail": "Document not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EmployeeDocumentSerializer(
            document
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="employee_document_archive",
        summary="Archive employee document",
        description=(
            "Archive an employee document. "
            "The document is not permanently deleted and can be restored."
        ),
        responses=EmployeeDocumentSerializer,
        tags=["Employee Documents"],
    )
    def delete(
        self,
        request,
        organization_id,
        employee_id,
        document_id,
    ):

        # -----------------------------------------
        # Get employee within request organization
        # -----------------------------------------

        try:
            employee = (
                EmployeeService
                .get_employee_for_organization(
                    employee_id=employee_id,
                    organization=request.organization,
                )
            )

        except Employee.DoesNotExist:
            return Response(
                {
                    "detail": "Employee not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -----------------------------------------
        # Get document
        # -----------------------------------------

        try:
            document = (
                EmployeeDocumentService
                .get_document(
                    employee=employee,
                    document_id=document_id,
                )
            )

        except EmployeeDocument.DoesNotExist:
            return Response(
                {
                    "detail": "Document not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -----------------------------------------
        # Archive document
        # -----------------------------------------

        try:
            EmployeeDocumentService.archive_document(
                document=document,
                organization=request.organization,
                archived_by=request.user,

            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

class EmployeeArchivedDocumentListView(APIView):

    permission_classes = [
        CanViewEmployeeDocuments,
    ]

    @extend_schema(
        operation_id="employee_archived_document_list",
        summary="List archived employee documents",
        description=(
            "Return all archived documents belonging to the specified employee."
        ),
        responses=EmployeeDocumentSerializer(many=True),
        tags=["Employee Documents"],
    )
    def get(
        self,
        request,
        organization_id,
        employee_id,
    ):

        try:

            employee = (
                EmployeeService
                .get_employee_for_organization(
                    employee_id=employee_id,
                    organization=request.organization,
                )
            )

        except Employee.DoesNotExist:

            return Response(
                {
                    "detail": "Employee not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        documents = (
            EmployeeDocumentService
            .list_archived_documents(
                employee=employee,
            )
        )

        serializer = EmployeeDocumentSerializer(
            documents,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class EmployeeDocumentRestoreView(APIView):

    permission_classes = [
        CanRestoreEmployeeDocuments,
    ]

    serializer_class = EmployeeDocumentSerializer
    @extend_schema(
        operation_id="employee_document_restore",
        summary="Restore employee document",
        description=(
            "Restore an archived employee document and make it active again."
        ),
        responses=EmployeeDocumentSerializer,
        tags=["Employee Documents"],
    )
    def post(
        self,
        request,
        organization_id,
        employee_id,
        document_id,
    ):

        try:

            employee = (
                EmployeeService
                .get_employee_for_organization(
                    employee_id=employee_id,
                    organization=request.organization,
                )
            )

        except Employee.DoesNotExist:

            return Response(
                {
                    "detail": "Employee not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:

            document = (
                EmployeeDocumentService
                .get_archived_document(
                    employee=employee,
                    document_id=document_id,
                )
            )

        except EmployeeDocument.DoesNotExist:

            return Response(
                {
                    "detail": "Archived document not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:

            document = (
                EmployeeDocumentService
                .restore_document(
                    document=document,
                    organization=request.organization,
                )
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EmployeeDocumentSerializer(
            document
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class EmployeeAccountProvisionView(APIView):

    permission_classes = [
        CanProvisionEmployeeAccounts,
    ]

    @extend_schema(
        operation_id="employee_account_provision",
        summary="Provision employee account",
        description=(
            "Create a user account for an existing employee, "
            "link the account to the employee, create the "
            "organization membership, assign the requested role, "
            "and require initial password setup."
        ),
        request=EmployeeAccountProvisionSerializer,
        responses={
            200: EmployeeSerializer,
            400: OpenApiResponse(
                description="Account could not be provisioned."
            ),
            404: OpenApiResponse(
                description="Employee not found."
            ),
        },
        tags=["Employee Accounts"],
    )
    def post(
        self,
        request,
        organization_id,
        employee_id,
    ):

        # -----------------------------------
        # Validate request
        # -----------------------------------

        request_serializer = (
            EmployeeAccountProvisionSerializer(
                data=request.data,
            )
        )

        request_serializer.is_valid(
            raise_exception=True,
        )

        role_code = (
            request_serializer.validated_data[
                "role_code"
            ]
        )

        # -----------------------------------
        # Get employee within organization
        # -----------------------------------

        try:

            employee = EmployeeService.get_employee(
                employee_id=employee_id,
                organization=request.organization,
            )

        except Employee.DoesNotExist:

            return Response(
                {
                    "detail": "Employee not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -----------------------------------
        # Provision account
        # -----------------------------------

        try:

            result = (
                EmployeeService
                .provision_employee_account(
                    employee=employee,
                    role_code=role_code,
                )
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------------
        # Return employee
        # -----------------------------------

        response_serializer = EmployeeSerializer(
            result["employee"],
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

class EmployeeAccountInviteView(APIView):

    permission_classes = [
        CanInviteEmployeeAccounts,
    ]

    @extend_schema(
        operation_id="employee_account_invite",
        summary="Send employee account invitation",
        description=(
            "Send or resend the password setup invitation "
            "for an existing employee account."
        ),
        request=None,
        responses={
            200: OpenApiResponse(
                description="Invitation sent successfully."
            ),
            400: OpenApiResponse(
                description="Employee account is not eligible "
                "for an invitation."
            ),
            404: OpenApiResponse(
                description="Employee not found."
            ),
        },
        tags=["Employee Accounts"],
    )
    def post(
        self,
        request,
        organization_id,
        employee_id,
    ):

        try:

            employee = EmployeeService.get_employee(
                employee_id=employee_id,
                organization=request.organization,
            )

        except Employee.DoesNotExist:

            return Response(
                {
                    "detail": "Employee not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if employee.user_id is None:

            return Response(
                {
                    "detail": (
                        "Employee does not have "
                        "an account."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            AccountService.send_password_setup_invitation(
                user=employee.user,
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Invitation sent successfully."
            },
            status=status.HTTP_200_OK,
        )

class EmployeeActivateView(APIView):

    permission_classes = [
        CanActivateEmployees,
    ]

    @extend_schema(
        operation_id="employee_activate",
        summary="Activate employee",
        description=(
            "Reactivate an inactive employee and restore "
            "their organization membership and account access."
        ),
        request=None,
        responses={
            200: EmployeeSerializer,
            400: OpenApiResponse(
                description="Employee is already active or "
                "cannot be activated."
            ),
            404: OpenApiResponse(
                description="Employee not found."
            ),
        },
        tags=["Employees"],
    )
    def post(
        self,
        request,
        organization_id,
        employee_id,
    ):

        try:

            employee = EmployeeService.get_employee(
                employee_id=employee_id,
                organization=request.organization,
            )

        except Employee.DoesNotExist:

            return Response(
                {
                    "detail": "Employee not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:

            employee = (
                EmployeeService
                .activate_employee(
                    employee=employee,
                )
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EmployeeSerializer(
            employee,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )