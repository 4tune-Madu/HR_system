from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from .models import Employee

class EmployeeListView(
    LoginRequiredMixin,
    TemplateView,
):

    template_name = "employee/employees/list.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        organization_id = self.kwargs[
            "organization_id"
        ]

        employees = (
            Employee.objects
            .filter(
                organization_id=organization_id,
                is_active=True,
            )
            .select_related(
                "identity",
                "contact",
                "assignment",
                "assignment__department",
                "assignment__position",
                "assignment__job_grade",
            )
        )

        context["employees"] = employees

        context["organization_id"] = organization_id

        return context