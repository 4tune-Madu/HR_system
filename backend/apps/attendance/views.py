from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    OpenApiTypes,
    OpenApiParameter,
)
from rest_framework import (
    status,
    serializers,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.exceptions import (
    NotFound,
    ValidationError,
)
from apps.employee.models import Employee
from apps.employee.services import EmployeeService

from .models import (
    AttendanceDevice,
    AttendanceRecord,
    AttendanceEvent,
    AttendanceSyncLog,
)
from apps.access.permissions import (
    CanViewAttendanceDevices,
    CanManageAttendanceDevices,
    CanManageAttendanceSettings,
    CanViewAttendanceRecords,
    CanManageManualAttendance,
    CanManageAttendanceReconciliation,
)
from .serializers import (
    AttendanceDeviceUserSerializer,
    AttendanceDeviceMappingSerializer,
    AttendanceDeviceMappingCreateSerializer,
    AttendanceDeviceMappingUpdateSerializer,
    AttendanceRecordSerializer,
    AttendanceEventSerializer,
    ManualAttendanceCheckInSerializer,
    AttendanceDeviceSyncSerializer,
    AttendanceSyncLogSerializer,
)
from .services import (
    AttendanceDeviceService,
    AttendanceEventService,
    AttendanceSyncService,
    AttendanceRecordService,
)


class AttendanceDeviceUsersView(
    APIView
):

    permission_classes = [
        CanViewAttendanceDevices,
    ]

    @extend_schema(
        operation_id="attendance_device_users",
        summary="List attendance device users",
        description=(
            "Retrieve users currently registered on the "
            "physical attendance device and show whether "
            "each device user is mapped to an employee."
        ),
        responses={
            200: AttendanceDeviceUserSerializer(
                many=True
            ),
            400: OpenApiResponse(
                description="Device cannot be accessed."
            ),
            404: OpenApiResponse(
                description="Attendance device not found."
            ),
        },
        tags=["Attendance Devices"],
    )
    def get(
        self,
        request,
        organization_id,
        device_id,
    ):
        try:

            device = (
                AttendanceDevice.objects
                .get(
                    id=device_id,
                    organization=request.organization,
                )
            )

        except AttendanceDevice.DoesNotExist:

            return Response(
                {
                    "detail": (
                        "Attendance device not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:

            device_users = (
                AttendanceDeviceService
                .get_device_users(
                    device=device,
                )
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        mappings = (
            AttendanceDeviceService
            .get_all_employee_mappings(
                device=device,
            )
        )

        mapping_by_user_id = {
            str(mapping.device_user_id): mapping
            for mapping in mappings
            if mapping.is_active
        }

        response_data = []

        for user in device_users:

            device_user_id = str(
                getattr(
                    user,
                    "user_id",
                    "",
                )
            )

            mapping = mapping_by_user_id.get(
                device_user_id
            )

            employee = (
                mapping.employee
                if mapping
                else None
            )

            identity = (
                getattr(
                    employee,
                    "identity",
                    None,
                )
                if employee
                else None
            )

            employee_name = None

            if identity:

                employee_name = " ".join(
                    part
                    for part in [
                        identity.first_name,
                        identity.middle_name,
                        identity.last_name,
                    ]
                    if part
                )

            response_data.append(
                {
                    "uid": getattr(
                        user,
                        "uid",
                        0,
                    ),
                    "user_id": device_user_id,
                    "name": getattr(
                        user,
                        "name",
                        "",
                    ),
                    "privilege": getattr(
                        user,
                        "privilege",
                        0,
                    ),
                    "card": str(
                        getattr(
                            user,
                            "card",
                            "",
                        )
                    ),
                    "mapped": mapping is not None,
                    "employee_id": (
                        employee.id
                        if employee
                        else None
                    ),
                    "employee_number": (
                        employee.employee_number
                        if employee
                        else None
                    ),
                    "employee_name": employee_name,
                }
            )

        serializer = (
            AttendanceDeviceUserSerializer(
                response_data,
                many=True,
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )



class AttendanceDeviceMappingListCreateView(
    APIView
):

    permission_classes = [
        CanViewAttendanceDevices,
    ]

    def get_permissions(self):

        if self.request.method == "POST":
            return [
                CanManageAttendanceDevices()
            ]

        return [
            CanViewAttendanceDevices()
        ]

    @extend_schema(
        operation_id="attendance_device_mapping_list",
        summary="List attendance device mappings",
        description=(
            "List all employee mappings configured for "
            "an attendance device."
        ),
        responses={
            200: AttendanceDeviceMappingSerializer(
                many=True
            ),
            404: OpenApiResponse(
                description="Attendance device not found."
            ),
        },
        tags=["Attendance Device Mappings"],
    )
    def get(
        self,
        request,
        organization_id,
        device_id,
    ):
        try:

            device = (
                AttendanceDevice.objects
                .get(
                    id=device_id,
                    organization=request.organization,
                )
            )

        except AttendanceDevice.DoesNotExist:

            return Response(
                {
                    "detail": (
                        "Attendance device not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        mappings = (
            AttendanceDeviceService
            .get_all_employee_mappings(
                device=device,
            )
        )

        serializer = (
            AttendanceDeviceMappingSerializer(
                mappings,
                many=True,
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="attendance_device_mapping_create",
        summary="Map attendance device user to employee",
        description=(
            "Map a device user ID from an attendance device "
            "to an employee belonging to the same organization."
        ),
        request=AttendanceDeviceMappingCreateSerializer,
        responses={
            201: AttendanceDeviceMappingSerializer,
            400: OpenApiResponse(
                description="Mapping could not be created."
            ),
            404: OpenApiResponse(
                description=(
                    "Attendance device or employee "
                    "not found."
                )
            ),
        },
        tags=["Attendance Device Mappings"],
    )
    def post(
        self,
        request,
        organization_id,
        device_id,
    ):
        try:

            device = (
                AttendanceDevice.objects
                .get(
                    id=device_id,
                    organization=request.organization,
                )
            )

        except AttendanceDevice.DoesNotExist:

            return Response(
                {
                    "detail": (
                        "Attendance device not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = (
            AttendanceDeviceMappingCreateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        employee_id = (
            serializer.validated_data[
                "employee_id"
            ]
        )

        device_user_id = (
            serializer.validated_data[
                "device_user_id"
            ]
        )

        display_name = (
            serializer.validated_data.get(
                "display_name",
                "",
            )
        )

        try:

            employee = (
                EmployeeService.get_employee(
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

            mapping = (
                AttendanceDeviceService
                .map_employee(
                    device=device,
                    employee=employee,
                    device_user_id=device_user_id,
                    display_name=display_name,
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
            AttendanceDeviceMappingSerializer(
                mapping,
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

        
class AttendanceDeviceMappingDetailView(
    APIView
):

    permission_classes = [
        CanViewAttendanceDevices,
    ]

    def get_permissions(self):

        if self.request.method in [
            "PATCH",
            "DELETE",
        ]:
            return [
                CanManageAttendanceDevices()
            ]

        return [
            CanViewAttendanceDevices()
        ]

    @extend_schema(
        operation_id="attendance_device_mapping_detail",
        summary="Get attendance device mapping",
        description=(
            "Retrieve the employee mapping for a specific "
            "device user ID."
        ),
        responses={
            200: AttendanceDeviceMappingSerializer,
            404: OpenApiResponse(
                description="Mapping not found."
            ),
        },
        tags=["Attendance Device Mappings"],
    )
    def get(
        self,
        request,
        organization_id,
        device_id,
        device_user_id,
    ):
        try:

            device = (
                AttendanceDevice.objects
                .get(
                    id=device_id,
                    organization=request.organization,
                )
            )

        except AttendanceDevice.DoesNotExist:

            return Response(
                {
                    "detail": (
                        "Attendance device not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        mapping = (
            AttendanceDeviceService
            .get_mapping(
                device=device,
                device_user_id=device_user_id,
            )
        )

        if mapping is None:

            return Response(
                {
                    "detail": (
                        "Attendance device mapping "
                        "not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = (
            AttendanceDeviceMappingSerializer(
                mapping,
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="attendance_device_mapping_remap",
        summary="Remap attendance device user",
        description=(
            "Change the employee associated with a "
            "device user ID."
        ),
        request=AttendanceDeviceMappingUpdateSerializer,
        responses={
            200: AttendanceDeviceMappingSerializer,
            400: OpenApiResponse(
                description="Mapping could not be updated."
            ),
            404: OpenApiResponse(
                description=(
                    "Attendance device or employee "
                    "not found."
                )
            ),
        },
        tags=["Attendance Device Mappings"],
    )
    def patch(
        self,
        request,
        organization_id,
        device_id,
        device_user_id,
    ):
        try:

            device = (
                AttendanceDevice.objects
                .get(
                    id=device_id,
                    organization=request.organization,
                )
            )

        except AttendanceDevice.DoesNotExist:

            return Response(
                {
                    "detail": (
                        "Attendance device not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        mapping = (
            AttendanceDeviceService
            .get_mapping(
                device=device,
                device_user_id=device_user_id,
            )
        )

        if mapping is None:

            return Response(
                {
                    "detail": (
                        "Attendance device mapping "
                        "not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = (
            AttendanceDeviceMappingUpdateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        employee_id = (
            serializer.validated_data[
                "employee_id"
            ]
        )

        display_name = (
            serializer.validated_data.get(
                "display_name",
                "",
            )
        )

        try:

            employee = (
                EmployeeService.get_employee(
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

            mapping = (
                AttendanceDeviceService
                .remap_employee(
                    device=device,
                    device_user_id=device_user_id,
                    employee=employee,
                    display_name=display_name,
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
            AttendanceDeviceMappingSerializer(
                mapping,
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="attendance_device_mapping_delete",
        summary="Unmap attendance device user",
        description=(
            "Deactivate the employee mapping for a "
            "device user ID. The historical mapping is "
            "retained."
        ),
        responses={
            204: OpenApiResponse(
                description="Mapping deactivated."
            ),
            400: OpenApiResponse(
                description="Mapping could not be deactivated."
            ),
            404: OpenApiResponse(
                description="Attendance device not found."
            ),
        },
        tags=["Attendance Device Mappings"],
    )
    def delete(
        self,
        request,
        organization_id,
        device_id,
        device_user_id,
    ):
        try:

            device = (
                AttendanceDevice.objects
                .get(
                    id=device_id,
                    organization=request.organization,
                )
            )

        except AttendanceDevice.DoesNotExist:

            return Response(
                {
                    "detail": (
                        "Attendance device not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:

            AttendanceDeviceService.unmap_employee(
                device=device,
                device_user_id=device_user_id,
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

class AttendanceRecordListView(ListAPIView):
    permission_classes = [CanViewAttendanceRecords]
    serializer_class = AttendanceRecordSerializer

    @extend_schema(
        tags=["Attendance Records"],
        parameters=[
            OpenApiParameter(
                name="employee_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Filter attendance records by employee UUID."
                ),
            ),
            OpenApiParameter(
                name="date_from",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Return records from this attendance date "
                    "onwards."
                ),
            ),
            OpenApiParameter(
                name="date_to",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Return records up to and including this "
                    "attendance date."
                ),
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Filter by attendance status."
                ),
                enum=[
                    choice[0]
                    for choice in AttendanceRecord.Status.choices
                ],
            ),
        ],
    )
    def get_queryset(self):
        records = (
            AttendanceRecord.objects
            .filter(
                organization=self.request.organization,
            )
            .select_related(
                "employee",
                "employee__identity",
            )
        )

        employee_id = self.request.query_params.get(
            "employee_id"
        )

        date_from = self.request.query_params.get(
            "date_from"
        )

        date_to = self.request.query_params.get(
            "date_to"
        )

        record_status = self.request.query_params.get(
            "status"
        )

        if employee_id:
            records = records.filter(
                employee_id=employee_id,
            )

        if date_from:
            records = records.filter(
                attendance_date__gte=date_from,
            )

        if date_to:
            records = records.filter(
                attendance_date__lte=date_to,
            )

        if record_status:
            records = records.filter(
                status=record_status,
            )

        return records.order_by(
            "-attendance_date",
            "employee__employee_number",
        )


class AttendanceRecordDetailView(RetrieveAPIView):
    permission_classes = [CanViewAttendanceRecords]
    serializer_class = AttendanceRecordSerializer
    lookup_url_kwarg = "record_id"

    @extend_schema(
        tags=["Attendance Records"],
    )
    def get_queryset(self):
        return (
            AttendanceRecord.objects
            .filter(
                organization=self.request.organization,
            )
            .select_related(
                "employee",
                "employee__identity",
            )
        )

class AttendanceRecordReconcileView(APIView):
    permission_classes = [
        CanManageAttendanceReconciliation
    ]

    @extend_schema(
        tags=["Attendance Records"],
        responses={
            200: AttendanceRecordSerializer,
        },
    )
    def post(
        self,
        request,
        organization_id,
        record_id,
    ):
        record = (
            AttendanceRecord.objects
            .filter(
                id=record_id,
                organization=request.organization,
            )
            .select_related(
                "employee",
                "employee__identity",
            )
            .first()
        )

        if record is None:
            raise NotFound(
                "Attendance record was not found "
                "in this organization."
            )

        reconciled_record = (
            AttendanceRecordService
            .reconcile_open_attendance_record(
                record=record,
            )
        )

        if reconciled_record is None:
            raise ValidationError(
                "Attendance record is not eligible "
                "for reconciliation."
            )

        return Response(
            AttendanceRecordSerializer(
                reconciled_record
            ).data,
            status=status.HTTP_200_OK,
        )

class AttendanceEventListView(ListAPIView):
    permission_classes = [CanViewAttendanceRecords]
    serializer_class = AttendanceEventSerializer

    @extend_schema(
        tags=["Attendance Events"],
        parameters=[
            OpenApiParameter(
                name="employee_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter events by employee UUID.",
            ),
            OpenApiParameter(
                name="device_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter events by attendance device UUID.",
            ),
            OpenApiParameter(
                name="event_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by attendance event type.",
                enum=[
                    choice[0]
                    for choice in AttendanceEvent.EventType.choices
                ],
            ),
            OpenApiParameter(
                name="source",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by event source.",
                enum=[
                    choice[0]
                    for choice in AttendanceEvent.Source.choices
                ],
            ),
            OpenApiParameter(
                name="processing_status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by event processing status.",
                enum=[
                    choice[0]
                    for choice in AttendanceEvent.ProcessingStatus.choices
                ],
            ),
            OpenApiParameter(
                name="date_from",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Return events occurring on or after this date.",
            ),
            OpenApiParameter(
                name="date_to",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Return events occurring on or before this date.",
            ),
        ],
    )
    def get_queryset(self):
        events = (
            AttendanceEvent.objects
            .filter(
                organization=self.request.organization,
            )
            .select_related(
                "employee",
                "employee__identity",
                "device",
            )
        )

        employee_id = self.request.query_params.get("employee_id")
        device_id = self.request.query_params.get("device_id")
        event_type = self.request.query_params.get("event_type")
        source = self.request.query_params.get("source")
        processing_status = self.request.query_params.get("processing_status")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        if employee_id:
            events = events.filter(
                employee_id=employee_id,
            )
        
        if device_id:
            events = events.filter(
                device_id = device_id,
            )

        if event_type:
            events = events.filter(
                event_type=event_type,
            )

        if source:
            events= events.filter(
                source = source,
            )

        if processing_status:
            events = events.filter(
                processing_status = processing_status,
            )
        
        if date_from:
            events = events.filter(
                occurred_at__date__gte=date_from,
            )

        if date_to:
            events = events.filter(
                occurred_at__date__lte=date_to,
            )

        
        return events.order_by("-occurred_at")


class AttendanceEventDetailView(RetrieveAPIView):
    permission_classes = [CanViewAttendanceRecords]
    serializer_class = AttendanceEventSerializer
    lookup_url_kwarg = "event_id"

    @extend_schema(
        tags=["Attendance Events"],
    )
    def get_queryset(self):
        return (
            AttendanceEvent.objects
            .filter(organization=self.request.organization)
            .select_related(
                "employee",
                "employee__identity",
                "device",
            )
        )

class ManualAttendanceCheckInView(APIView):
    permission_classes = [
        CanManageManualAttendance
    ]

    @extend_schema(
        tags=["Attendance"],
        request=ManualAttendanceCheckInSerializer,
        responses={
            201: AttendanceEventSerializer,
        },
    )
    def post(
        self,
        request,
        organization_id,
    ):
        serializer = (
            ManualAttendanceCheckInSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        employee_id = serializer.validated_data[
            "employee_id"
        ]

        employee = (
            Employee.objects
            .filter(
                id=employee_id,
                organization=request.organization,
            )
            .first()
        )

        if employee is None:
            raise NotFound(
                "Employee was not found "
                "in this organization."
            )

        try:
            event = (
                AttendanceEventService
                .manual_check_in(
                    organization=request.organization,
                    employee=employee,
                    occurred_at=(
                        serializer.validated_data.get(
                            "occurred_at"
                        )
                    ),
                )
            )

        except ValueError as exc:
            raise ValidationError(
                str(exc)
            )

        return Response(
            AttendanceEventSerializer(event).data,
            status=status.HTTP_201_CREATED,
        )


class AttendanceDeviceSyncView(APIView):
    permission_classes = [
        CanManageAttendanceDevices
    ]

    @extend_schema(
        tags=["Attendance"],
        request=AttendanceDeviceSyncSerializer,
        responses={
            200: AttendanceSyncLogSerializer,
        },
    )
    def post(
        self,
        request,
        organization_id,
        device_id,
    ):
        serializer = (
            AttendanceDeviceSyncSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        device = (
            AttendanceDevice.objects
            .filter(
                id=device_id,
                organization=request.organization,
            )
            .first()
        )

        if device is None:
            raise NotFound(
                "Attendance device was not found "
                "in this organization."
            )

        if not device.is_active:
            raise serializers.ValidationError(
                "Attendance device is inactive."
            )

        try:
            sync_log = (
                AttendanceSyncService.run_sync(
                    device=device,
                    start_date=(
                        serializer.validated_data.get(
                            "start_date"
                        )
                    ),
                    end_date=(
                        serializer.validated_data.get(
                            "end_date"
                        )
                    ),
                    trigger=(
                        AttendanceSyncLog
                        .Trigger
                        .API
                    ),
                )
            )

        except Exception as exc:
            from rest_framework.exceptions import APIException

            error = APIException(
                detail=(
                    f"Attendance device synchronization "
                    f"failed: {exc}"
                )
            )
            error.status_code = 502
            raise error

        return Response(
            AttendanceSyncLogSerializer(
                sync_log
            ).data,
            status=status.HTTP_200_OK,
        )