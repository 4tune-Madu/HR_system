from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView

from apps.access.permissions import CanManageAttendanceSettings, CanManageOrganizationStructure, CanViewOrganization
from apps.organization.models import Branch, Department, JobGrade, Organization, Position, Team
from apps.organization.serializers import (
    BranchSerializer,
    DepartmentSerializer,
    JobGradeSerializer,
    OrganizationAttendanceSettingsSerializer,
    PositionSerializer,
    TeamSerializer,
)


class OrganizationAttendanceSettingsView(RetrieveUpdateAPIView):
    serializer_class = OrganizationAttendanceSettingsSerializer
    permission_classes = [CanManageAttendanceSettings]

    def get_queryset(self):
        return Organization.objects.filter(is_active=True)

    def get_object(self):
        return self.get_queryset().get(id=self.kwargs["organization_id"])


class OrganizationStructureMixin:
    permission_classes = [CanManageOrganizationStructure]

    def get_permissions(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return [(CanViewOrganization | CanManageOrganizationStructure)()]
        return super().get_permissions()


class BranchListCreateView(OrganizationStructureMixin, ListCreateAPIView):
    serializer_class = BranchSerializer

    def get_queryset(self):
        return Branch.objects.filter(organization=self.request.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization)


class BranchDetailView(OrganizationStructureMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = BranchSerializer

    def get_queryset(self):
        return Branch.objects.filter(organization=self.request.organization)

    def perform_update(self, serializer):
        serializer.save(organization=self.request.organization)


class DepartmentListCreateView(OrganizationStructureMixin, ListCreateAPIView):
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        return Department.objects.filter(organization=self.request.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization)


class DepartmentDetailView(OrganizationStructureMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        return Department.objects.filter(organization=self.request.organization)

    def perform_update(self, serializer):
        serializer.save(organization=self.request.organization)


class TeamListCreateView(OrganizationStructureMixin, ListCreateAPIView):
    serializer_class = TeamSerializer

    def get_queryset(self):
        return Team.objects.filter(department__organization=self.request.organization)

    def perform_create(self, serializer):
        department = serializer.validated_data["department"]
        if department.organization_id != self.request.organization.id:
            raise ValidationError({"department": "Department is outside this organization."})
        serializer.save()


class TeamDetailView(OrganizationStructureMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = TeamSerializer

    def get_queryset(self):
        return Team.objects.filter(department__organization=self.request.organization)

    def perform_update(self, serializer):
        department = serializer.validated_data.get("department")
        if department and department.organization_id != self.request.organization.id:
            raise ValidationError({"department": "Department is outside this organization."})
        serializer.save()


class JobGradeListCreateView(OrganizationStructureMixin, ListCreateAPIView):
    serializer_class = JobGradeSerializer

    def get_queryset(self):
        return JobGrade.objects.filter(organization=self.request.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization)


class JobGradeDetailView(OrganizationStructureMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = JobGradeSerializer

    def get_queryset(self):
        return JobGrade.objects.filter(organization=self.request.organization)

    def perform_update(self, serializer):
        serializer.save(organization=self.request.organization)


class PositionListCreateView(OrganizationStructureMixin, ListCreateAPIView):
    serializer_class = PositionSerializer

    def get_queryset(self):
        return Position.objects.filter(organization=self.request.organization)

    def _validate_related_objects(self, serializer):
        department = serializer.validated_data.get("department")
        job_grade = serializer.validated_data.get("job_grade")
        if department and department.organization_id != self.request.organization.id:
            raise ValidationError({"department": "Department is outside this organization."})
        if job_grade and job_grade.organization_id != self.request.organization.id:
            raise ValidationError({"job_grade": "Job grade is outside this organization."})

    def perform_create(self, serializer):
        self._validate_related_objects(serializer)
        serializer.save(organization=self.request.organization)


class PositionDetailView(OrganizationStructureMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = PositionSerializer

    def get_queryset(self):
        return Position.objects.filter(organization=self.request.organization)

    def perform_update(self, serializer):
        PositionListCreateView._validate_related_objects(self, serializer)
        serializer.save(organization=self.request.organization)
