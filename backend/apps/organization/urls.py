from django.urls import path

from apps.organization.views import (
    BranchDetailView,
    BranchListCreateView,
    DepartmentDetailView,
    DepartmentListCreateView,
    JobGradeDetailView,
    JobGradeListCreateView,
    OrganizationAttendanceSettingsView,
    PositionDetailView,
    PositionListCreateView,
    TeamDetailView,
    TeamListCreateView,
)


urlpatterns = [
    path("<uuid:organization_id>/attendance/settings/", OrganizationAttendanceSettingsView.as_view()),
    path("<uuid:organization_id>/branches/", BranchListCreateView.as_view()),
    path("<uuid:organization_id>/branches/<uuid:pk>/", BranchDetailView.as_view()),
    path("<uuid:organization_id>/departments/", DepartmentListCreateView.as_view()),
    path("<uuid:organization_id>/departments/<uuid:pk>/", DepartmentDetailView.as_view()),
    path("<uuid:organization_id>/teams/", TeamListCreateView.as_view()),
    path("<uuid:organization_id>/teams/<uuid:pk>/", TeamDetailView.as_view()),
    path("<uuid:organization_id>/job-grades/", JobGradeListCreateView.as_view()),
    path("<uuid:organization_id>/job-grades/<uuid:pk>/", JobGradeDetailView.as_view()),
    path("<uuid:organization_id>/positions/", PositionListCreateView.as_view()),
    path("<uuid:organization_id>/positions/<uuid:pk>/", PositionDetailView.as_view()),
]
