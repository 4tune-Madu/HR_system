from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    extend_schema_field,
)

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.permissions import (
    HasOrganizationPermission,
)

from apps.employee.models import Employee

from .models import (
    LeaveRequest,
    LeaveType,
    LeaveBalance,
    LeavePolicy,
    PublicHoliday,
    WorkSchedule,
    LeaveAccrual,
    LeaveApprovalRule,
    LeaveApprovalStep
    
)

from apps.access.permissions import (
    CanViewLeave,
    CanRequestLeave,
    CanApproveLeave,
    CanManageLeave,
)
from .serializers import (
    LeaveRequestSerializer,
    LeaveRequestCreateSerializer,
    LeaveRequestReviewSerializer,
    LeaveTypeSerializer,
    LeaveTypeWriteSerializer,
    LeavePolicySerializer,
    LeavePolicyWriteSerializer,
    LeaveBalanceSerializer,
    WorkScheduleSerializer,
    WorkScheduleWriteSerializer,
    PublicHolidaySerializer,
    PublicHolidayWriteSerializer,
    EmployeeWorkScheduleSerializer,
    EmployeeWorkScheduleWriteSerializer,
    LeaveEntitlementSerializer,
    LeaveEntitlementWriteSerializer,
    LeaveBalanceAdjustmentSerializer,
    LeaveBalanceAdjustmentWriteSerializer,
    LeaveAccrualSerializer,
    LeaveApprovalRuleSerializer,
    LeaveApprovalRuleWriteSerializer,
    LeaveApprovalStepSerializer,
)
from .services import (
    LeaveRequestService,
    LeaveTypeService,
    LeavePolicyService,
    PublicHolidayService,
    WorkScheduleService,
    EmployeeWorkScheduleService,
    LeaveEntitlementService,
    LeaveBalanceAdjustmentService,
    LeaveApprovalRuleService
)


class LeaveRequestListView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave()
            ]

        if self.request.method == "POST":
            return [
                CanRequestLeave()
            ]

        return []

    @extend_schema(
        operation_id="leave_request_list",
        summary="List leave requests",
        description=(
            "List leave requests belonging to the "
            "specified organization."
        ),
        responses=LeaveRequestSerializer(
            many=True
        ),
        tags=["Leave"],
    )
    def get(
        self,
        request,
        organization_id,
    ):

        requests = (
            LeaveRequest.objects
            .filter(
                employee__organization=(
                    request.organization
                )
            )
            .select_related(
                "employee",
                "employee__identity",
                "leave_type",
                "reviewed_by",
            )
            .order_by(
                "-created_at"
            )
        )

        serializer = LeaveRequestSerializer(
            requests,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="leave_request_create",
        summary="Create leave request",
        description=(
            "Create a draft leave request for the "
            "authenticated employee."
        ),
        request=LeaveRequestCreateSerializer,
        responses={
            201: LeaveRequestSerializer,
            400: OpenApiResponse(
                description="Invalid leave request."
            ),
        },
        tags=["Leave"],
    )
    def post(
        self,
        request,
        organization_id,
    ):

        serializer = LeaveRequestCreateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:

            employee = Employee.objects.get(
                user=request.user,
                organization=request.organization,
                is_active=True,
            )

        except Employee.DoesNotExist:

            return Response(
                {
                    "detail": (
                        "You do not have an active "
                        "employee record in this organization."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            leave_type = LeaveType.objects.get(
                id=serializer.validated_data[
                    "leave_type"
                ],
                organization=request.organization,
            )

        except LeaveType.DoesNotExist:

            return Response(
                {
                    "detail": "Leave type not found."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            leave_request = (
                LeaveRequestService
                .create_request(
                    employee=employee,
                    leave_type=leave_type,
                    organization=request.organization,
                    start_date=serializer.validated_data[
                        "start_date"
                    ],
                    end_date=serializer.validated_data[
                        "end_date"
                    ],
                    reason=serializer.validated_data.get(
                        "reason",
                        "",
                    ),
                )
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = LeaveRequestSerializer(
            leave_request,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class LeaveRequestDetailView(APIView):

    permission_classes = [
        CanViewLeave,
    ]

    @extend_schema(
        operation_id="leave_request_detail",
        summary="Get leave request",
        responses=LeaveRequestSerializer,
        tags=["Leave"],
    )
    def get(
        self,
        request,
        organization_id,
        request_id,
    ):

        try:

            leave_request = (
                LeaveRequest.objects
                .select_related(
                    "employee",
                    "employee__identity",
                    "leave_type",
                    "reviewed_by",
                )
                .get(
                    id=request_id,
                    employee__organization=(
                        request.organization
                    ),
                )
            )

        except LeaveRequest.DoesNotExist:

            return Response(
                {
                    "detail": "Leave request not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LeaveRequestSerializer(
            leave_request,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class LeaveRequestSubmitView(APIView):

    permission_classes = [
        CanRequestLeave,
    ]

    @extend_schema(
        operation_id="leave_request_submit",
        summary="Submit leave request",
        description=(
            "Submit a draft leave request for approval."
        ),
        request=None,
        responses={
            200: LeaveRequestSerializer,
            400: OpenApiResponse(
                description=(
                    "Leave request cannot be submitted."
                ),
            ),
            403: OpenApiResponse(
                description=(
                    "The authenticated user does not own "
                    "this leave request."
                ),
            ),
            404: OpenApiResponse(
                description="Leave request not found.",
            ),
        },
        tags=["Leave"],
    )
    def post(
        self,
        request,
        organization_id,
        request_id,
    ):

        try:

            leave_request = (
                LeaveRequest.objects
                .get(
                    id=request_id,
                    employee__organization=(
                        request.organization
                    ),
                )
            )

        except LeaveRequest.DoesNotExist:

            return Response(
                {
                    "detail": "Leave request not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Only the employee who owns the request
        # can submit it.

        if (
            leave_request.employee.user_id
            != request.user.id
        ):
            return Response(
                {
                    "detail": "You cannot submit this leave request."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:

            leave_request = (
                LeaveRequestService
                .submit_request(
                    leave_request=leave_request,
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

        serializer = LeaveRequestSerializer(
            leave_request,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class LeaveRequestApproveView(APIView):

    permission_classes = [
        CanApproveLeave,
    ]

    @extend_schema(
        operation_id="leave_request_approve",
        summary="Approve leave request",
        request=LeaveRequestReviewSerializer,
        responses=LeaveRequestSerializer,
        tags=["Leave"],
    )
    def post(
        self,
        request,
        organization_id,
        request_id,
    ):

        serializer = LeaveRequestReviewSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:

            leave_request = (
                LeaveRequest.objects
                .get(
                    id=request_id,
                    employee__organization=(
                        request.organization
                    ),
                )
            )

        except LeaveRequest.DoesNotExist:

            return Response(
                {
                    "detail": "Leave request not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:

            leave_request = (
                LeaveRequestService
                .approve_request(
                    leave_request=leave_request,
                    reviewed_by=request.user,
                    organization=request.organization,
                    review_comment=(
                        serializer.validated_data.get(
                            "review_comment",
                            "",
                        )
                    ),
                )
            )

        except PermissionError as exc:

            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        except (
            ValueError,
            LeaveBalance.DoesNotExist,
        ) as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = LeaveRequestSerializer(
            leave_request,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class LeaveRequestRejectView(APIView):

    permission_classes = [
        CanApproveLeave,
    ]

    @extend_schema(
        operation_id="leave_request_reject",
        summary="Reject leave request",
        request=LeaveRequestReviewSerializer,
        responses=LeaveRequestSerializer,
        tags=["Leave"],
    )
    def post(
        self,
        request,
        organization_id,
        request_id,
    ):

        serializer = LeaveRequestReviewSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:

            leave_request = (
                LeaveRequest.objects
                .get(
                    id=request_id,
                    employee__organization=(
                        request.organization
                    ),
                )
            )

        except LeaveRequest.DoesNotExist:

            return Response(
                {
                    "detail": "Leave request not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:

            leave_request = (
                LeaveRequestService
                .reject_request(
                    leave_request=leave_request,
                    reviewed_by=request.user,
                    organization=request.organization,
                    review_comment=(
                        serializer.validated_data.get(
                            "review_comment",
                            "",
                        )
                    ),
                )
            )

        except PermissionError as exc:

            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        except ValueError as exc:            

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = LeaveRequestSerializer(
            leave_request,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class LeaveRequestCancelView(APIView):

    permission_classes = [
        CanRequestLeave,
    ]

    @extend_schema(
        operation_id="leave_request_cancel",
        summary="Cancel leave request",
         request=None,
        responses={
            200: LeaveRequestSerializer,
            400: OpenApiResponse(
                description=(
                    "Leave request cannot be cancelled."
                ),
            ),
            403: OpenApiResponse(
                description=(
                    "The authenticated user does not own "
                    "this leave request."
                ),
            ),
            404: OpenApiResponse(
                description="Leave request not found.",
            ),
        },
        tags=["Leave"],
    )
    def post(
        self,
        request,
        organization_id,
        request_id,
    ):

        try:

            leave_request = (
                LeaveRequest.objects
                .get(
                    id=request_id,
                    employee__organization=(
                        request.organization
                    ),
                )
            )

        except LeaveRequest.DoesNotExist:

            return Response(
                {
                    "detail": "Leave request not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            leave_request.employee.user_id
            != request.user.id
        ):
            return Response(
                {
                    "detail": "You cannot cancel this leave request."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:

            leave_request = (
                LeaveRequestService
                .cancel_request(
                    leave_request=leave_request,
                )
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = LeaveRequestSerializer(
            leave_request,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class LeaveTypeListView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "POST":
            return [
                CanManageLeave(),
            ]

        return []

    @extend_schema(
        operation_id="leave_type_list",
        summary="List leave types",
        description=(
            "List leave types configured for the organization."
        ),
        responses=LeaveTypeSerializer(many=True),
        tags=["Leave Administration"],
    )
    def get(
        self,
        request,
        organization_id,
    ):

        leave_types = (
            LeaveType.objects
            .filter(
                organization=request.organization,
            )
            .order_by(
                "name",
            )
        )

        serializer = LeaveTypeSerializer(
            leave_types,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="leave_type_create",
        summary="Create leave type",
        request=LeaveTypeWriteSerializer,
        responses={
            201: LeaveTypeSerializer,
            400: OpenApiResponse(
                description="Invalid leave type.",
            ),
        },
        tags=["Leave Administration"],
    )
    def post(
        self,
        request,
        organization_id,
    ):

        serializer = LeaveTypeWriteSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            leave_type = (
                LeaveTypeService
                .create_leave_type(
                    organization=request.organization,
                    **serializer.validated_data,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = LeaveTypeSerializer(
            leave_type,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

class LeaveTypeDetailView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "PATCH":
            return [
                CanManageLeave(),
            ]

        return []

    def get_object(
        self,
        request,
        leave_type_id,
    ):

        try:
            return LeaveType.objects.get(
                id=leave_type_id,
                organization=request.organization,
            )

        except LeaveType.DoesNotExist:
            return None

    @extend_schema(
        operation_id="leave_type_detail",
        summary="Get leave type",
        responses={
            200: LeaveTypeSerializer,
            404: OpenApiResponse(
                description="Leave type not found.",
            ),
        },
        tags=["Leave Administration"],
    )
    def get(
        self,
        request,
        organization_id,
        leave_type_id,
    ):

        leave_type = self.get_object(
            request,
            leave_type_id,
        )

        if leave_type is None:
            return Response(
                {
                    "detail": "Leave type not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LeaveTypeSerializer(
            leave_type,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="leave_type_update",
        summary="Update leave type",
        request=LeaveTypeWriteSerializer,
        responses={
            200: LeaveTypeSerializer,
            400: OpenApiResponse(
                description="Invalid leave type.",
            ),
            404: OpenApiResponse(
                description="Leave type not found.",
            ),
        },
        tags=["Leave Administration"],
    )
    def patch(
        self,
        request,
        organization_id,
        leave_type_id,
    ):

        leave_type = self.get_object(
            request,
            leave_type_id,
        )

        if leave_type is None:
            return Response(
                {
                    "detail": "Leave type not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LeaveTypeWriteSerializer(
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        try:
            leave_type = (
                LeaveTypeService
                .update_leave_type(
                    leave_type=leave_type,
                    organization=request.organization,
                    code=data.get(
                        "code",
                        leave_type.code,
                    ),
                    name=data.get(
                        "name",
                        leave_type.name,
                    ),
                    description=data.get(
                        "description",
                        leave_type.description,
                    ),
                    is_paid=data.get(
                        "is_paid",
                        leave_type.is_paid,
                    ),
                    requires_approval=data.get(
                        "requires_approval",
                        leave_type.requires_approval,
                    ),
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = LeaveTypeSerializer(
            leave_type,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

class LeaveTypeActivateView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    @extend_schema(
        operation_id="leave_type_activate",
        summary="Activate leave type",
        request=None,
        responses={
            200: LeaveTypeSerializer,
            400: OpenApiResponse(
                description=(
                    "Leave type is already active "
                    "or cannot be activated."
                ),
            ),
            404: OpenApiResponse(
                description="Leave type not found.",
            ),
        },
        tags=["Leave Administration"],
    )
    def post(
        self,
        request,
        organization_id,
        leave_type_id,
    ):

        try:
            leave_type = LeaveType.objects.get(
                id=leave_type_id,
                organization=request.organization,
            )

        except LeaveType.DoesNotExist:
            return Response(
                {
                    "detail": "Leave type not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            leave_type = (
                LeaveTypeService
                .activate_leave_type(
                    leave_type=leave_type,
                    organization=request.organization,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = LeaveTypeSerializer(
            leave_type,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class LeaveTypeDeactivateView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    @extend_schema(
        operation_id="leave_type_deactivate",
        summary="Deactivate leave type",
        request=None,
        responses={
            200: LeaveTypeSerializer,
            400: OpenApiResponse(
                description=(
                    "Leave type is already inactive "
                    "or cannot be deactivated."
                ),
            ),
            404: OpenApiResponse(
                description="Leave type not found.",
            ),
        },
        tags=["Leave Administration"],
    )
    def post(
        self,
        request,
        organization_id,
        leave_type_id,
    ):

        try:
            leave_type = LeaveType.objects.get(
                id=leave_type_id,
                organization=request.organization,
            )

        except LeaveType.DoesNotExist:
            return Response(
                {
                    "detail": "Leave type not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            leave_type = (
                LeaveTypeService
                .deactivate_leave_type(
                    leave_type=leave_type,
                    organization=request.organization,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = LeaveTypeSerializer(
            leave_type,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class LeavePolicyListView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "POST":
            return [
                CanManageLeave(),
            ]

        return []

    @extend_schema(
        operation_id="leave_policy_list",
        summary="List leave policies",
        responses=LeavePolicySerializer(many=True),
        tags=["Leave Administration"],
    )
    def get(
        self,
        request,
        organization_id,
    ):

        policies = (
            LeavePolicy.objects
            .filter(
                organization=request.organization,
            )
            .select_related(
                "leave_type",
            )
            .order_by(
                "leave_type__name",
            )
        )

        serializer = LeavePolicySerializer(
            policies,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="leave_policy_create",
        summary="Create leave policy",
        request=LeavePolicyWriteSerializer,
        responses={
            201: LeavePolicySerializer,
            400: OpenApiResponse(
                description="Invalid leave policy.",
            ),
        },
        tags=["Leave Administration"],
    )
    def post(
        self,
        request,
        organization_id,
    ):

        serializer = LeavePolicyWriteSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        try:
            leave_type = LeaveType.objects.get(
                id=data["leave_type"],
                organization=request.organization,
            )

        except LeaveType.DoesNotExist:
            return Response(
                {
                    "detail": "Leave type not found.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data.pop("leave_type")

        try:
            policy = (
                LeavePolicyService
                .create_policy(
                    organization=request.organization,
                    leave_type=leave_type,
                    **data,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = LeavePolicySerializer(
            policy,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

class LeavePolicyDetailView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "PATCH":
            return [
                CanManageLeave(),
            ]

        return []

    def get_object(
        self,
        request,
        policy_id,
    ):

        try:
            return (
                LeavePolicy.objects
                .select_related(
                    "leave_type",
                )
                .get(
                    id=policy_id,
                    organization=request.organization,
                )
            )

        except LeavePolicy.DoesNotExist:
            return None

    @extend_schema(
        operation_id="leave_policy_detail",
        summary="Get leave policy",
        responses=LeavePolicySerializer,
        tags=["Leave Administration"],
    )
    def get(
        self,
        request,
        organization_id,
        policy_id,
    ):

        policy = self.get_object(
            request,
            policy_id,
        )

        if policy is None:
            return Response(
                {
                    "detail": "Leave policy not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LeavePolicySerializer(
            policy,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="leave_policy_update",
        summary="Update leave policy",
        request=LeavePolicyWriteSerializer,
        responses=LeavePolicySerializer,
        tags=["Leave Administration"],
    )
    def patch(
        self,
        request,
        organization_id,
        policy_id,
    ):

        policy = self.get_object(
            request,
            policy_id,
        )

        if policy is None:
            return Response(
                {
                    "detail": "Leave policy not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LeavePolicyWriteSerializer(
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        data.pop(
            "leave_type",
            None,
        )

        try:
            policy = (
                LeavePolicyService
                .update_policy(
                    policy=policy,
                    organization=request.organization,
                    days_per_year=data.get(
                        "days_per_year",
                        policy.days_per_year,
                    ),
                    minimum_days_per_request=data.get(
                        "minimum_days_per_request",
                        policy.minimum_days_per_request,
                    ),
                    maximum_days_per_request=data.get(
                        "maximum_days_per_request",
                        policy.maximum_days_per_request,
                    ),
                    allow_half_day=data.get(
                        "allow_half_day",
                        policy.allow_half_day,
                    ),
                    allow_carry_forward=data.get(
                        "allow_carry_forward",
                        policy.allow_carry_forward,
                    ),
                    maximum_carry_forward_days=data.get(
                        "maximum_carry_forward_days",
                        policy.maximum_carry_forward_days,
                    ),
                    requires_attachment=data.get(
                        "requires_attachment",
                        policy.requires_attachment,
                    ),
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = LeavePolicySerializer(
            policy,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

class LeavePolicyActivateView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    @extend_schema(
        operation_id="leave_policy_activate",
        summary="Activate leave policy",
        request=None,
        responses={
            200: LeavePolicySerializer,
            400: OpenApiResponse(
                description=(
                    "Leave policy is already active "
                    "or cannot be activated."
                ),
            ),
            404: OpenApiResponse(
                description="Leave policy not found.",
            ),
        },
        tags=["Leave Administration"],
    )
    def post(
        self,
        request,
        organization_id,
        policy_id,
    ):

        try:
            policy = LeavePolicy.objects.get(
                id=policy_id,
                organization=request.organization,
            )

        except LeavePolicy.DoesNotExist:
            return Response(
                {
                    "detail": "Leave policy not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            policy = (
                LeavePolicyService
                .activate_policy(
                    policy=policy,
                    organization=request.organization,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = LeavePolicySerializer(
            policy,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class LeavePolicyDeactivateView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    @extend_schema(
        operation_id="leave_policy_deactivate",
        summary="Deactivate leave policy",
        request=None,
        responses={
            200: LeavePolicySerializer,
            400: OpenApiResponse(
                description=(
                    "Leave policy is already inactive "
                    "or cannot be deactivated."
                ),
            ),
            404: OpenApiResponse(
                description="Leave policy not found.",
            ),
        },
        tags=["Leave Administration"],
    )
    def post(
        self,
        request,
        organization_id,
        policy_id,
    ):

        try:
            policy = LeavePolicy.objects.get(
                id=policy_id,
                organization=request.organization,
            )

        except LeavePolicy.DoesNotExist:
            return Response(
                {
                    "detail": "Leave policy not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            policy = (
                LeavePolicyService
                .deactivate_policy(
                    policy=policy,
                    organization=request.organization,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = LeavePolicySerializer(
            policy,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class LeaveApprovalRuleListView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "POST":
            return [
                CanManageLeave(),
            ]

        return []

    @extend_schema(
        operation_id="leave_approval_rule_list",
        summary="List leave approval rules",
        responses=LeaveApprovalRuleSerializer(
            many=True
        ),
        tags=["Leave Approval"],
    )
    def get(
        self,
        request,
        organization_id,
    ):

        rules = (
            LeaveApprovalRule.objects
            .filter(
                organization=request.organization,
            )
            .select_related(
                "leave_type",
            )
            .order_by(
                "leave_type__name",
                "approval_level",
            )
        )

        return Response(
            LeaveApprovalRuleSerializer(
                rules,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="leave_approval_rule_create",
        summary="Create leave approval rule",
        request=LeaveApprovalRuleWriteSerializer,
        responses={
            201: LeaveApprovalRuleSerializer,
            400: OpenApiResponse(
                description="Invalid approval rule.",
            ),
        },
        tags=["Leave Approval"],
    )
    def post(
        self,
        request,
        organization_id,
    ):

        serializer = (
            LeaveApprovalRuleWriteSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        leave_type = None

        if "leave_type" in data:
            try:
                leave_type = (
                    LeaveType.objects.get(
                        id=data["leave_type"],
                        organization=request.organization,
                    )
                )
            except LeaveType.DoesNotExist:
                return Response(
                    {
                        "detail": "Leave type not found.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        try:
            rule = (
                LeaveApprovalRuleService
                .create_rule(
                    organization=request.organization,
                    leave_type=leave_type,
                    approval_level=data[
                        "approval_level"
                    ],
                    minimum_days=data.get(
                        "minimum_days",
                        Decimal("0"),
                    ),
                    maximum_days=data.get(
                        "maximum_days",
                    ),
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            LeaveApprovalRuleSerializer(
                rule
            ).data,
            status=status.HTTP_201_CREATED,
        )

class LeaveApprovalRuleDetailView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "PATCH":
            return [
                CanManageLeave(),
            ]

        return []

    def get_object(
        self,
        request,
        rule_id,
    ):
        try:
            return (
                LeaveApprovalRule.objects
                .select_related(
                    "leave_type",
                )
                .get(
                    id=rule_id,
                    organization=request.organization,
                )
            )
        except LeaveApprovalRule.DoesNotExist:
            return None

    @extend_schema(
        operation_id="leave_approval_rule_detail",
        summary="Get leave approval rule",
        responses={
            200: LeaveApprovalRuleSerializer,
            404: OpenApiResponse(
                description="Approval rule not found.",
            ),
        },
        tags=["Leave Approval"],
    )
    def get(
        self,
        request,
        organization_id,
        rule_id,
    ):

        rule = self.get_object(
            request,
            rule_id,
        )

        if rule is None:
            return Response(
                {
                    "detail": "Approval rule not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            LeaveApprovalRuleSerializer(
                rule
            ).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="leave_approval_rule_update",
        summary="Update leave approval rule",
        request=LeaveApprovalRuleWriteSerializer,
        responses={
            200: LeaveApprovalRuleSerializer,
            400: OpenApiResponse(
                description="Invalid approval rule.",
            ),
        },
        tags=["Leave Approval"],
    )
    def patch(
        self,
        request,
        organization_id,
        rule_id,
    ):

        rule = self.get_object(
            request,
            rule_id,
        )

        if rule is None:
            return Response(
                {
                    "detail": "Approval rule not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = (
            LeaveApprovalRuleWriteSerializer(
                data=request.data,
                partial=True,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        leave_type = rule.leave_type

        if "leave_type" in data:

            if data["leave_type"] is None:
                leave_type = None

            else:
                try:
                    leave_type = (
                        LeaveType.objects.get(
                            id=data["leave_type"],
                            organization=request.organization,
                        )
                    )
                except LeaveType.DoesNotExist:
                    return Response(
                        {
                            "detail": "Leave type not found.",
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )

        try:
            rule = (
                LeaveApprovalRuleService
                .update_rule(
                    rule=rule,
                    organization=request.organization,
                    leave_type=leave_type,
                    approval_level=data.get(
                        "approval_level",
                        rule.approval_level,
                    ),
                    minimum_days=data.get(
                        "minimum_days",
                        rule.minimum_days,
                    ),
                    maximum_days=data.get(
                        "maximum_days",
                        rule.maximum_days,
                    ),
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            LeaveApprovalRuleSerializer(
                rule
            ).data,
            status=status.HTTP_200_OK,
        )

class LeaveApprovalRuleActivateView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    @extend_schema(
        operation_id="leave_approval_rule_activate",
        summary="Activate leave approval rule",
        responses=LeaveApprovalRuleSerializer,
        tags=["Leave Approval"],
    )
    def post(
        self,
        request,
        organization_id,
        rule_id,
    ):

        try:
            rule = (
                LeaveApprovalRule.objects.get(
                    id=rule_id,
                    organization=request.organization,
                )
            )
        except LeaveApprovalRule.DoesNotExist:
            return Response(
                {
                    "detail": "Approval rule not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            rule = (
                LeaveApprovalRuleService
                .activate_rule(
                    rule=rule,
                    organization=request.organization,
                )
            )
        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            LeaveApprovalRuleSerializer(
                rule
            ).data,
            status=status.HTTP_200_OK,
        )

class LeaveApprovalRuleDeactivateView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    @extend_schema(
        operation_id="leave_approval_rule_deactivate",
        summary="Deactivate leave approval rule",
        responses=LeaveApprovalRuleSerializer,
        tags=["Leave Approval"],
    )
    def post(
        self,
        request,
        organization_id,
        rule_id,
    ):

        try:
            rule = (
                LeaveApprovalRule.objects.get(
                    id=rule_id,
                    organization=request.organization,
                )
            )
        except LeaveApprovalRule.DoesNotExist:
            return Response(
                {
                    "detail": "Approval rule not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            rule = (
                LeaveApprovalRuleService
                .deactivate_rule(
                    rule=rule,
                    organization=request.organization,
                )
            )
        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            LeaveApprovalRuleSerializer(
                rule
            ).data,
            status=status.HTTP_200_OK,
        )

class LeaveBalanceListView(APIView):

    permission_classes = [
        CanViewLeave,
    ]

    @extend_schema(
        operation_id="leave_balance_list",
        summary="List organization leave balances",
        description=(
            "List leave balances for active employees "
            "within the organization."
        ),
        responses=LeaveBalanceSerializer(many=True),
        tags=["Leave"],
    )
    def get(
        self,
        request,
        organization_id,
    ):

        balances = (
            LeaveBalance.objects
            .filter(
                employee__organization=(
                    request.organization
                ),
                employee__is_active=True,
            )
            .select_related(
                "employee",
                "employee__identity",
                "leave_type",
            )
            .order_by(
                "employee__employee_number",
                "leave_type__name",
                "-year",
            )
        )

        serializer = LeaveBalanceSerializer(
            balances,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class LeaveBalanceDetailView(APIView):

    permission_classes = [
        CanViewLeave,
    ]

    @extend_schema(
        operation_id="leave_balance_detail",
        summary="Get leave balance",
        responses={
            200: LeaveBalanceSerializer,
            404: OpenApiResponse(
                description="Leave balance not found."
            ),
        },
        tags=["Leave"],
    )
    def get(
        self,
        request,
        organization_id,
        balance_id,
    ):

        try:

            balance = (
                LeaveBalance.objects
                .select_related(
                    "employee",
                    "employee__identity",
                    "leave_type",
                )
                .get(
                    id=balance_id,
                    employee__organization=(
                        request.organization
                    ),
                )
            )

        except LeaveBalance.DoesNotExist:

            return Response(
                {
                    "detail": "Leave balance not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LeaveBalanceSerializer(
            balance,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class EmployeeLeaveBalanceListView(APIView):

    permission_classes = [
        CanViewLeave,
    ]

    @extend_schema(
        operation_id="employee_leave_balance_list",
        summary="List employee leave balances",
        description=(
            "List all leave balances for a specific employee "
            "within the organization."
        ),
        responses=LeaveBalanceSerializer(many=True),
        tags=["Leave"],
    )
    def get(
        self,
        request,
        organization_id,
        employee_id,
    ):

        balances = (
            LeaveBalance.objects
            .filter(
                employee_id=employee_id,
                employee__organization=(
                    request.organization
                ),
            )
            .select_related(
                "employee",
                "employee__identity",
                "leave_type",
            )
            .order_by(
                "-year",
                "leave_type__name",
            )
        )

        serializer = LeaveBalanceSerializer(
            balances,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class WorkScheduleListView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "POST":
            return [
                CanManageLeave(),
            ]

        return []

    @extend_schema(
        operation_id="work_schedule_list",
        summary="List work schedules",
        responses=WorkScheduleSerializer(
            many=True
        ),
        tags=["Leave Calendar"],
    )
    def get(
        self,
        request,
        organization_id,
    ):

        schedules = (
            WorkSchedule.objects
            .filter(
                organization=request.organization,
            )
            .order_by(
                "-is_default",
                "name",
            )
        )

        serializer = WorkScheduleSerializer(
            schedules,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="work_schedule_create",
        summary="Create work schedule",
        request=WorkScheduleWriteSerializer,
        responses={
            201: WorkScheduleSerializer,
            400: OpenApiResponse(
                description="Invalid work schedule."
            ),
        },
        tags=["Leave Calendar"],
    )
    def post(
        self,
        request,
        organization_id,
    ):

        serializer = WorkScheduleWriteSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            schedule = (
                WorkScheduleService
                .create_schedule(
                    organization=request.organization,
                    **serializer.validated_data,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = (
            WorkScheduleSerializer(
                schedule
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

class WorkScheduleDetailView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "PATCH":
            return [
                CanManageLeave(),
            ]

        return []

    def get_object(
        self,
        request,
        schedule_id,
    ):

        try:
            return WorkSchedule.objects.get(
                id=schedule_id,
                organization=request.organization,
            )
        except WorkSchedule.DoesNotExist:
            return None

    @extend_schema(
        operation_id="work_schedule_detail",
        summary="Get work schedule",
        responses=WorkScheduleSerializer,
        tags=["Leave Calendar"],
    )
    def get(
        self,
        request,
        organization_id,
        schedule_id,
    ):

        schedule = self.get_object(
            request,
            schedule_id,
        )

        if schedule is None:
            return Response(
                {
                    "detail": "Work schedule not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            WorkScheduleSerializer(
                schedule
            ).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="work_schedule_update",
        summary="Update work schedule",
        request=WorkScheduleWriteSerializer,
        responses=WorkScheduleSerializer,
        tags=["Leave Calendar"],
    )
    def patch(
        self,
        request,
        organization_id,
        schedule_id,
    ):

        schedule = self.get_object(
            request,
            schedule_id,
        )

        if schedule is None:
            return Response(
                {
                    "detail": "Work schedule not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = WorkScheduleWriteSerializer(
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        try:
            schedule = (
                WorkScheduleService
                .update_schedule(
                    schedule=schedule,
                    organization=request.organization,
                    code=data.get(
                        "code",
                        schedule.code,
                    ),
                    name=data.get(
                        "name",
                        schedule.name,
                    ),
                    monday=data.get(
                        "monday",
                        schedule.monday,
                    ),
                    tuesday=data.get(
                        "tuesday",
                        schedule.tuesday,
                    ),
                    wednesday=data.get(
                        "wednesday",
                        schedule.wednesday,
                    ),
                    thursday=data.get(
                        "thursday",
                        schedule.thursday,
                    ),
                    friday=data.get(
                        "friday",
                        schedule.friday,
                    ),
                    saturday=data.get(
                        "saturday",
                        schedule.saturday,
                    ),
                    sunday=data.get(
                        "sunday",
                        schedule.sunday,
                    ),
                    is_default=data.get(
                        "is_default",
                        schedule.is_default,
                    ),
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            WorkScheduleSerializer(
                schedule
            ).data,
            status=status.HTTP_200_OK,
        )


class WorkScheduleActivateView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    @extend_schema(
        operation_id="work_schedule_activate",
        summary="Activate work schedule",
        responses=WorkScheduleSerializer,
        tags=["Leave Calendar"],
    )
    def post(
        self,
        request,
        organization_id,
        schedule_id,
    ):

        try:
            schedule = WorkSchedule.objects.get(
                id=schedule_id,
                organization=request.organization,
            )
        except WorkSchedule.DoesNotExist:
            return Response(
                {
                    "detail": "Work schedule not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            schedule = (
                WorkScheduleService
                .activate_schedule(
                    schedule=schedule,
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

        return Response(
            WorkScheduleSerializer(
                schedule
            ).data,
            status=status.HTTP_200_OK,
        )

class WorkScheduleDeactivateView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    @extend_schema(
        operation_id="work_schedule_deactivate",
        summary="Deactivate work schedule",
        responses=WorkScheduleSerializer,
        tags=["Leave Calendar"],
    )
    def post(
        self,
        request,
        organization_id,
        schedule_id,
    ):

        try:
            schedule = WorkSchedule.objects.get(
                id=schedule_id,
                organization=request.organization,
            )
        except WorkSchedule.DoesNotExist:
            return Response(
                {
                    "detail": "Work schedule not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            schedule = (
                WorkScheduleService
                .deactivate_schedule(
                    schedule=schedule,
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

        return Response(
            WorkScheduleSerializer(
                schedule
            ).data,
            status=status.HTTP_200_OK,
        )

class WorkScheduleSetDefaultView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    @extend_schema(
        operation_id="work_schedule_set_default",
        summary="Set default work schedule",
        responses=WorkScheduleSerializer,
        tags=["Leave Calendar"],
    )
    def post(
        self,
        request,
        organization_id,
        schedule_id,
    ):

        try:
            schedule = WorkSchedule.objects.get(
                id=schedule_id,
                organization=request.organization,
            )
        except WorkSchedule.DoesNotExist:
            return Response(
                {
                    "detail": "Work schedule not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            schedule = (
                WorkScheduleService
                .set_default_schedule(
                    schedule=schedule,
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

        return Response(
            WorkScheduleSerializer(
                schedule
            ).data,
            status=status.HTTP_200_OK,
        )

class PublicHolidayListView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "POST":
            return [
                CanManageLeave(),
            ]

        return []

    @extend_schema(
        operation_id="public_holiday_list",
        summary="List public holidays",
        responses=PublicHolidaySerializer(
            many=True
        ),
        tags=["Leave Calendar"],
    )
    def get(
        self,
        request,
        organization_id,
    ):

        holidays = (
            PublicHoliday.objects
            .filter(
                organization=request.organization,
            )
            .order_by(
                "date",
            )
        )

        return Response(
            PublicHolidaySerializer(
                holidays,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="public_holiday_create",
        summary="Create public holiday",
        request=PublicHolidayWriteSerializer,
        responses={
            201: PublicHolidaySerializer,
            400: OpenApiResponse(
                description="Invalid public holiday."
            ),
        },
        tags=["Leave Calendar"],
    )
    def post(
        self,
        request,
        organization_id,
    ):

        serializer = PublicHolidayWriteSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            holiday = (
                PublicHolidayService
                .create_holiday(
                    organization=request.organization,
                    **serializer.validated_data,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PublicHolidaySerializer(
                holiday
            ).data,
            status=status.HTTP_201_CREATED,
        )

class PublicHolidayDetailView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "PATCH":
            return [
                CanManageLeave(),
            ]

        return []

    def get_object(
        self,
        request,
        holiday_id,
    ):

        try:
            return PublicHoliday.objects.get(
                id=holiday_id,
                organization=request.organization,
            )
        except PublicHoliday.DoesNotExist:
            return None

    @extend_schema(
        operation_id="public_holiday_detail",
        summary="Get public holiday",
        responses=PublicHolidaySerializer,
        tags=["Leave Calendar"],
    )
    def get(
        self,
        request,
        organization_id,
        holiday_id,
    ):

        holiday = self.get_object(
            request,
            holiday_id,
        )

        if holiday is None:
            return Response(
                {
                    "detail": "Public holiday not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            PublicHolidaySerializer(
                holiday
            ).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="public_holiday_update",
        summary="Update public holiday",
        request=PublicHolidayWriteSerializer,
        responses=PublicHolidaySerializer,
        tags=["Leave Calendar"],
    )
    def patch(
        self,
        request,
        organization_id,
        holiday_id,
    ):

        holiday = self.get_object(
            request,
            holiday_id,
        )

        if holiday is None:
            return Response(
                {
                    "detail": "Public holiday not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PublicHolidayWriteSerializer(
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        try:
            holiday = (
                PublicHolidayService
                .update_holiday(
                    holiday=holiday,
                    organization=request.organization,
                    date=data.get(
                        "date",
                        holiday.date,
                    ),
                    name=data.get(
                        "name",
                        holiday.name,
                    ),
                    description=data.get(
                        "description",
                        holiday.description,
                    ),
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PublicHolidaySerializer(
                holiday
            ).data,
            status=status.HTTP_200_OK,
        )

class PublicHolidayActivateView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

class PublicHolidayActivateView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    @extend_schema(
        operation_id="public_holiday_activate",
        summary="Activate public holiday",
        description=(
            "Activate a public holiday for the specified "
            "organization. An active holiday is excluded "
            "from working-day leave calculations."
        ),
        responses={
            200: PublicHolidaySerializer,
            400: OpenApiResponse(
                description=(
                    "Public holiday is already active "
                    "or cannot be activated."
                ),
            ),
            404: OpenApiResponse(
                description="Public holiday not found.",
            ),
        },
        tags=["Leave Calendar"],
    )
    def post(
        self,
        request,
        organization_id,
        holiday_id,
    ):

        try:
            holiday = PublicHoliday.objects.get(
                id=holiday_id,
                organization=request.organization,
            )

        except PublicHoliday.DoesNotExist:
            return Response(
                {
                    "detail": "Public holiday not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            holiday = (
                PublicHolidayService
                .activate_holiday(
                    holiday=holiday,
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

        return Response(
            PublicHolidaySerializer(
                holiday
            ).data,
            status=status.HTTP_200_OK,
        )


class PublicHolidayDeactivateView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    @extend_schema(
        operation_id="public_holiday_deactivate",
        summary="Deactivate public holiday",
        description=(
            "Deactivate a public holiday for the specified "
            "organization. A deactivated holiday is no longer "
            "excluded from working-day leave calculations."
        ),
        responses={
            200: PublicHolidaySerializer,
            400: OpenApiResponse(
                description=(
                    "Public holiday is already inactive "
                    "or cannot be deactivated."
                ),
            ),
            404: OpenApiResponse(
                description="Public holiday not found.",
            ),
        },
        tags=["Leave Calendar"],
    )
    def post(
        self,
        request,
        organization_id,
        holiday_id,
    ):

        try:
            holiday = PublicHoliday.objects.get(
                id=holiday_id,
                organization=request.organization,
            )

        except PublicHoliday.DoesNotExist:
            return Response(
                {
                    "detail": "Public holiday not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            holiday = (
                PublicHolidayService
                .deactivate_holiday(
                    holiday=holiday,
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

        return Response(
            PublicHolidaySerializer(
                holiday
            ).data,
            status=status.HTTP_200_OK,
        )

class EmployeeWorkScheduleListView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "POST":
            return [
                CanManageLeave(),
            ]

        return []

    def get_employee(
        self,
        request,
        employee_id,
    ):
        try:
            return Employee.objects.get(
                id=employee_id,
                organization=request.organization,
            )
        except Employee.DoesNotExist:
            return None

    @extend_schema(
        operation_id="employee_work_schedule_list",
        summary="List employee work schedules",
        description=(
            "List work schedule assignments for an employee."
        ),
        responses=EmployeeWorkScheduleSerializer(
            many=True,
        ),
        tags=["Leave Calendar"],
    )
    def get(
        self,
        request,
        organization_id,
        employee_id,
    ):

        employee = self.get_employee(
            request,
            employee_id,
        )

        if employee is None:
            return Response(
                {
                    "detail": "Employee not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        assignments = (
            EmployeeWorkSchedule.objects
            .filter(
                employee=employee,
            )
            .select_related(
                "employee",
                "employee__identity",
                "work_schedule",
            )
            .order_by(
                "-effective_from",
            )
        )

        serializer = EmployeeWorkScheduleSerializer(
            assignments,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="employee_work_schedule_assign",
        summary="Assign employee work schedule",
        request=EmployeeWorkScheduleWriteSerializer,
        responses={
            201: EmployeeWorkScheduleSerializer,
            400: OpenApiResponse(
                description="Invalid schedule assignment.",
            ),
            404: OpenApiResponse(
                description="Employee or work schedule not found.",
            ),
        },
        tags=["Leave Calendar"],
    )
    def post(
        self,
        request,
        organization_id,
        employee_id,
    ):

        employee = self.get_employee(
            request,
            employee_id,
        )

        if employee is None:
            return Response(
                {
                    "detail": "Employee not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = (
            EmployeeWorkScheduleWriteSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            work_schedule = (
                WorkSchedule.objects.get(
                    id=serializer.validated_data[
                        "work_schedule"
                    ],
                    organization=request.organization,
                )
            )

        except WorkSchedule.DoesNotExist:
            return Response(
                {
                    "detail": "Work schedule not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            assignment = (
                EmployeeWorkScheduleService
                .assign_schedule(
                    employee=employee,
                    work_schedule=work_schedule,
                    effective_from=serializer.validated_data[
                        "effective_from"
                    ],
                    effective_to=serializer.validated_data.get(
                        "effective_to"
                    ),
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            EmployeeWorkScheduleSerializer(
                assignment,
            ).data,
            status=status.HTTP_201_CREATED,
        )

class EmployeeWorkScheduleDetailView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    def get_object(
        self,
        request,
        employee_id,
        assignment_id,
    ):

        try:
            return (
                EmployeeWorkSchedule.objects
                .select_related(
                    "employee",
                    "employee__identity",
                    "work_schedule",
                )
                .get(
                    id=assignment_id,
                    employee_id=employee_id,
                    employee__organization=(
                        request.organization
                    ),
                )
            )

        except EmployeeWorkSchedule.DoesNotExist:
            return None

    @extend_schema(
        operation_id="employee_work_schedule_detail",
        summary="Get employee work schedule assignment",
        responses={
            200: EmployeeWorkScheduleSerializer,
            404: OpenApiResponse(
                description="Assignment not found.",
            ),
        },
        tags=["Leave Calendar"],
    )
    def get(
        self,
        request,
        organization_id,
        employee_id,
        assignment_id,
    ):

        assignment = self.get_object(
            request,
            employee_id,
            assignment_id,
        )

        if assignment is None:
            return Response(
                {
                    "detail": "Schedule assignment not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            EmployeeWorkScheduleSerializer(
                assignment,
            ).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="employee_work_schedule_update",
        summary="Update employee work schedule assignment",
        request=EmployeeWorkScheduleWriteSerializer,
        responses={
            200: EmployeeWorkScheduleSerializer,
            400: OpenApiResponse(
                description="Invalid schedule assignment.",
            ),
            404: OpenApiResponse(
                description="Assignment or work schedule not found.",
            ),
        },
        tags=["Leave Calendar"],
    )
    def patch(
        self,
        request,
        organization_id,
        employee_id,
        assignment_id,
    ):

        assignment = self.get_object(
            request,
            employee_id,
            assignment_id,
        )

        if assignment is None:
            return Response(
                {
                    "detail": "Schedule assignment not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        employee = assignment.employee

        serializer = (
            EmployeeWorkScheduleWriteSerializer(
                data=request.data,
                partial=True,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        try:
            work_schedule = (
                WorkSchedule.objects.get(
                    id=data.get(
                        "work_schedule",
                        assignment.work_schedule_id,
                    ),
                    organization=request.organization,
                )
            )

        except WorkSchedule.DoesNotExist:
            return Response(
                {
                    "detail": "Work schedule not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            assignment = (
                EmployeeWorkScheduleService
                .update_assignment(
                    assignment=assignment,
                    employee=employee,
                    work_schedule=work_schedule,
                    effective_from=data.get(
                        "effective_from",
                        assignment.effective_from,
                    ),
                    effective_to=data.get(
                        "effective_to",
                        assignment.effective_to,
                    ),
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            EmployeeWorkScheduleSerializer(
                assignment,
            ).data,
            status=status.HTTP_200_OK,
        )

class EmployeeWorkScheduleActivateView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    @extend_schema(
        operation_id="employee_work_schedule_activate",
        summary="Activate employee work schedule",
        responses={
            200: EmployeeWorkScheduleSerializer,
            400: OpenApiResponse(
                description="Assignment is already active.",
            ),
            404: OpenApiResponse(
                description="Assignment not found.",
            ),
        },
        tags=["Leave Calendar"],
    )
    def post(
        self,
        request,
        organization_id,
        employee_id,
        assignment_id,
    ):

        try:
            assignment = (
                EmployeeWorkSchedule.objects
                .get(
                    id=assignment_id,
                    employee_id=employee_id,
                    employee__organization=(
                        request.organization
                    ),
                )
            )

        except EmployeeWorkSchedule.DoesNotExist:
            return Response(
                {
                    "detail": "Schedule assignment not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            assignment = (
                EmployeeWorkScheduleService
                .activate_assignment(
                    assignment=assignment,
                    employee=assignment.employee,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            EmployeeWorkScheduleSerializer(
                assignment,
            ).data,
            status=status.HTTP_200_OK,
        )

class EmployeeWorkScheduleDeactivateView(APIView):

    permission_classes = [
        CanManageLeave,
    ]

    @extend_schema(
        operation_id="employee_work_schedule_deactivate",
        summary="Deactivate employee work schedule",
        responses={
            200: EmployeeWorkScheduleSerializer,
            400: OpenApiResponse(
                description="Assignment is already inactive.",
            ),
            404: OpenApiResponse(
                description="Assignment not found.",
            ),
        },
        tags=["Leave Calendar"],
    )
    def post(
        self,
        request,
        organization_id,
        employee_id,
        assignment_id,
    ):

        try:
            assignment = (
                EmployeeWorkSchedule.objects
                .get(
                    id=assignment_id,
                    employee_id=employee_id,
                    employee__organization=(
                        request.organization
                    ),
                )
            )

        except EmployeeWorkSchedule.DoesNotExist:
            return Response(
                {
                    "detail": "Schedule assignment not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            assignment = (
                EmployeeWorkScheduleService
                .deactivate_assignment(
                    assignment=assignment,
                    employee=assignment.employee,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            EmployeeWorkScheduleSerializer(
                assignment,
            ).data,
            status=status.HTTP_200_OK,
        )

class EmployeeLeaveEntitlementListView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "POST":
            return [
                CanManageLeave(),
            ]

        return []

    def get_employee(
        self,
        request,
        employee_id,
    ):
        try:
            return Employee.objects.get(
                id=employee_id,
                organization=request.organization,
            )
        except Employee.DoesNotExist:
            return None

    @extend_schema(
        operation_id="employee_leave_entitlement_list",
        summary="List employee leave entitlements",
        responses=LeaveEntitlementSerializer(
            many=True,
        ),
        tags=["Leave Entitlements"],
    )
    def get(
        self,
        request,
        organization_id,
        employee_id,
    ):

        employee = self.get_employee(
            request,
            employee_id,
        )

        if employee is None:
            return Response(
                {
                    "detail": "Employee not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        entitlements = (
            LeaveEntitlement.objects
            .filter(
                employee=employee,
            )
            .select_related(
                "employee",
                "employee__identity",
                "leave_type",
            )
            .order_by(
                "-year",
                "leave_type__name",
            )
        )

        serializer = LeaveEntitlementSerializer(
            entitlements,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="employee_leave_entitlement_create",
        summary="Create employee leave entitlement",
        request=LeaveEntitlementWriteSerializer,
        responses={
            201: LeaveEntitlementSerializer,
            400: OpenApiResponse(
                description="Invalid entitlement.",
            ),
            404: OpenApiResponse(
                description="Employee or leave type not found.",
            ),
        },
        tags=["Leave Entitlements"],
    )
    def post(
        self,
        request,
        organization_id,
        employee_id,
    ):

        employee = self.get_employee(
            request,
            employee_id,
        )

        if employee is None:
            return Response(
                {
                    "detail": "Employee not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LeaveEntitlementWriteSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        try:
            leave_type = LeaveType.objects.get(
                id=data["leave_type"],
                organization=request.organization,
            )
        except LeaveType.DoesNotExist:
            return Response(
                {
                    "detail": "Leave type not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        data.pop("leave_type")

        try:
            entitlement = (
                LeaveEntitlementService
                .create_entitlement(
                    employee=employee,
                    leave_type=leave_type,
                    **data,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            LeaveEntitlementSerializer(
                entitlement,
            ).data,
            status=status.HTTP_201_CREATED,
        )

class EmployeeLeaveEntitlementDetailView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "PATCH":
            return [
                CanManageLeave(),
            ]

        return []

    def get_object(
        self,
        request,
        employee_id,
        entitlement_id,
    ):

        try:
            return (
                LeaveEntitlement.objects
                .select_related(
                    "employee",
                    "employee__identity",
                    "leave_type",
                )
                .get(
                    id=entitlement_id,
                    employee_id=employee_id,
                    employee__organization=(
                        request.organization
                    ),
                )
            )
        except LeaveEntitlement.DoesNotExist:
            return None

    @extend_schema(
        operation_id="employee_leave_entitlement_detail",
        summary="Get employee leave entitlement",
        responses={
            200: LeaveEntitlementSerializer,
            404: OpenApiResponse(
                description="Entitlement not found.",
            ),
        },
        tags=["Leave Entitlements"],
    )
    def get(
        self,
        request,
        organization_id,
        employee_id,
        entitlement_id,
    ):

        entitlement = self.get_object(
            request,
            employee_id,
            entitlement_id,
        )

        if entitlement is None:
            return Response(
                {
                    "detail": "Leave entitlement not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            LeaveEntitlementSerializer(
                entitlement,
            ).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="employee_leave_entitlement_update",
        summary="Update employee leave entitlement",
        request=LeaveEntitlementWriteSerializer,
        responses={
            200: LeaveEntitlementSerializer,
            400: OpenApiResponse(
                description="Invalid entitlement.",
            ),
            404: OpenApiResponse(
                description="Entitlement or leave type not found.",
            ),
        },
        tags=["Leave Entitlements"],
    )
    def patch(
        self,
        request,
        organization_id,
        employee_id,
        entitlement_id,
    ):

        entitlement = self.get_object(
            request,
            employee_id,
            entitlement_id,
        )

        if entitlement is None:
            return Response(
                {
                    "detail": "Leave entitlement not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LeaveEntitlementWriteSerializer(
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        try:
            leave_type = LeaveType.objects.get(
                id=data.get(
                    "leave_type",
                    entitlement.leave_type_id,
                ),
                organization=request.organization,
            )
        except LeaveType.DoesNotExist:
            return Response(
                {
                    "detail": "Leave type not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            entitlement = (
                LeaveEntitlementService
                .update_entitlement(
                    entitlement=entitlement,
                    employee=entitlement.employee,
                    leave_type=leave_type,
                    year=data.get(
                        "year",
                        entitlement.year,
                    ),
                    days=data.get(
                        "days",
                        entitlement.days,
                    ),
                    is_override=data.get(
                        "is_override",
                        entitlement.is_override,
                    ),
                    reason=data.get(
                        "reason",
                        entitlement.reason,
                    ),
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            LeaveEntitlementSerializer(
                entitlement,
            ).data,
            status=status.HTTP_200_OK,
        )

class LeaveBalanceAdjustmentListView(APIView):

    def get_permissions(self):

        if self.request.method == "GET":
            return [
                CanViewLeave(),
            ]

        if self.request.method == "POST":
            return [
                CanManageLeave(),
            ]

        return []

    def get_balance(
        self,
        request,
        balance_id,
    ):

        try:
            return (
                LeaveBalance.objects
                .select_related(
                    "employee",
                    "employee__identity",
                    "leave_type",
                )
                .get(
                    id=balance_id,
                    employee__organization=(
                        request.organization
                    ),
                )
            )

        except LeaveBalance.DoesNotExist:
            return None

    @extend_schema(
        operation_id="leave_balance_adjustment_list",
        summary="List leave balance adjustments",
        responses=LeaveBalanceAdjustmentSerializer(
            many=True,
        ),
        tags=["Leave Balances"],
    )
    def get(
        self,
        request,
        organization_id,
        balance_id,
    ):

        balance = self.get_balance(
            request,
            balance_id,
        )

        if balance is None:
            return Response(
                {
                    "detail": "Leave balance not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        adjustments = (
            balance.adjustments
            .select_related(
                "adjusted_by",
            )
            .order_by(
                "-adjusted_at",
            )
        )

        serializer = LeaveBalanceAdjustmentSerializer(
            adjustments,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="leave_balance_adjustment_create",
        summary="Create leave balance adjustment",
        description=(
            "Create an auditable credit or debit adjustment "
            "against an employee's leave balance."
        ),
        request=LeaveBalanceAdjustmentWriteSerializer,
        responses={
            201: LeaveBalanceAdjustmentSerializer,
            400: OpenApiResponse(
                description="Invalid adjustment.",
            ),
            404: OpenApiResponse(
                description="Leave balance not found.",
            ),
        },
        tags=["Leave Balances"],
    )
    def post(
        self,
        request,
        organization_id,
        balance_id,
    ):

        balance = self.get_balance(
            request,
            balance_id,
        )

        if balance is None:
            return Response(
                {
                    "detail": "Leave balance not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = (
            LeaveBalanceAdjustmentWriteSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:

            adjustment = (
                LeaveBalanceAdjustmentService
                .create_adjustment(
                    balance=balance,
                    organization=request.organization,
                    adjusted_by=request.user,
                    amount=serializer.validated_data[
                        "amount"
                    ],
                    adjustment_type=(
                        serializer.validated_data[
                            "adjustment_type"
                        ]
                    ),
                    reason=serializer.validated_data[
                        "reason"
                    ],
                )
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            LeaveBalanceAdjustmentSerializer(
                adjustment,
            ).data,
            status=status.HTTP_201_CREATED,
        )

class LeaveAccrualListView(APIView):

    permission_classes = [
        CanViewLeave,
    ]

    @extend_schema(
        operation_id="leave_accrual_list",
        summary="List leave accrual history",
        description=(
            "List all accrual records associated with "
            "a leave balance."
        ),
        responses=LeaveAccrualSerializer(
            many=True,
        ),
        tags=["Leave Balances"],
    )
    def get(
        self,
        request,
        organization_id,
        balance_id,
    ):

        try:
            balance = (
                LeaveBalance.objects
                .get(
                    id=balance_id,
                    employee__organization=(
                        request.organization
                    ),
                )
            )

        except LeaveBalance.DoesNotExist:

            return Response(
                {
                    "detail": "Leave balance not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        accruals = (
            LeaveAccrual.objects
            .filter(
                balance=balance,
            )
            .order_by(
                "-year",
                "-period_month",
            )
        )

        serializer = LeaveAccrualSerializer(
            accruals,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )