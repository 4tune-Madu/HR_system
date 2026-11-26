from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from apps.access.permissions import HasOrganizationPermission
from apps.employee.models import Employee
from .models import OnboardingTask
from .serializers import OnboardingTaskSerializer


class CanViewOnboarding(HasOrganizationPermission):
    required_permission = "employee.view"


class CanManageOnboarding(HasOrganizationPermission):
    required_permission = "employee.update"


class OnboardingTaskListCreateView(ListCreateAPIView):
    serializer_class = OnboardingTaskSerializer

    def get_permissions(self):
        return [CanManageOnboarding() if self.request.method == "POST" else CanViewOnboarding()]

    def get_queryset(self):
        tasks = OnboardingTask.objects.filter(organization=self.request.organization).select_related("employee__identity")
        employee_id = self.request.query_params.get("employee_id")
        return tasks.filter(employee_id=employee_id) if employee_id else tasks

    def perform_create(self, serializer):
        employee = Employee.objects.filter(id=serializer.validated_data["employee"].id, organization=self.request.organization).first()
        if employee is None:
            raise ValidationError({"employee": "Employee was not found in this organization."})
        serializer.save(organization=self.request.organization, employee=employee)


class OnboardingTaskDetailView(RetrieveUpdateAPIView):
    serializer_class = OnboardingTaskSerializer
    lookup_url_kwarg = "task_id"

    def get_permissions(self):
        return [CanManageOnboarding() if self.request.method in {"PUT", "PATCH"} else CanViewOnboarding()]

    def get_queryset(self):
        return OnboardingTask.objects.filter(organization=self.request.organization).select_related("employee__identity")
