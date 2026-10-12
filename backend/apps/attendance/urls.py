from django.urls import path

from .views import (
    AttendanceDeviceMappingDetailView,
    AttendanceDeviceMappingListCreateView,
    AttendanceDeviceUsersView,
    AttendanceRecordListView,
    AttendanceRecordDetailView,
    AttendanceEventListView,
    AttendanceEventDetailView,
    ManualAttendanceCheckInView,
    AttendanceDeviceSyncView,
    AttendanceRecordReconcileView,
)


urlpatterns = [
    path(
        "organizations/<uuid:organization_id>/attendance/devices/<uuid:device_id>/users/",
        AttendanceDeviceUsersView.as_view(),
        name="attendance-device-users",
    ),

    path(
        "organizations/<uuid:organization_id>/attendance/devices/<uuid:device_id>/mappings/",
        AttendanceDeviceMappingListCreateView.as_view(),
        name="attendance-device-mappings",
    ),

    path(
        "organizations/<uuid:organization_id>/attendance/devices/<uuid:device_id>/mappings/<str:device_user_id>/",
        AttendanceDeviceMappingDetailView.as_view(),
        name="attendance-device-mapping-detail",
    ),

    path(
        "organizations/<uuid:organization_id>/attendance/records/",
        AttendanceRecordListView.as_view(),
        name="attendance-records",
    ),

    path(
        "organizations/<uuid:organization_id>/attendance/records/<uuid:record_id>/",
        AttendanceRecordDetailView.as_view(),
        name="attendance-record-detail",
    ),

    path(
        "organizations/<uuid:organization_id>/attendance/events/",
        AttendanceEventListView.as_view(),
        name="attendance-events",
    ),

    path(
        "organizations/<uuid:organization_id>/attendance/events/<uuid:event_id>/",
        AttendanceEventDetailView.as_view(),
        name="attendance-event-detail",
    ),

    path(
        "organizations/<uuid:organization_id>/attendance/manual/check-in/",
        ManualAttendanceCheckInView.as_view(),
        name="attendance-manual-check-in",
    ),

    path(
        "organizations/<uuid:organization_id>/attendance/devices/<uuid:device_id>/sync/",
        AttendanceDeviceSyncView.as_view(),
        name="attendance-device-sync",
    ),

    path(
        "organizations/<uuid:organization_id>/attendance/records/<uuid:record_id>/reconcile/",
        AttendanceRecordReconcileView.as_view(),
        name="attendance-record-reconcile",
    ),
]