from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views import View
from .models import (
    Employee,
    Organization,
    EmployeeDocument,
)
from .forms import (
    EmployeeDocumentUploadForm,
    EmployeeIdentityForm,
    EmployeeContactForm,
    EmployeeEmploymentForm,
)
from .services import (
    EmployeeDocumentService,
)

from apps.access.web_permissions import (
    OrganizationPermissionRequiredMixin,
)

class EmployeeListView(
    OrganizationPermissionRequiredMixin,
    View,
):
    required_permission = "employee.view"

    def get(
        self,
        request,
        organization_id,
    ):

        organization = get_object_or_404(
            Organization,
            id=organization_id,
        )

        employees = (
            Employee.objects
            .filter(
                organization=organization,
            )
            .select_related(
                "identity",
                "contact",
                "assignment",
                "assignment__department",
                "assignment__position",
                "assignment__job_grade",
                "employment",
            )
            .order_by(
                "employee_number"
            )
        )

        return render(
            request,
            "employee/employees/list.html",
            {
                "employees": employees,
                "organization": organization,
            },
        )

class  EmployeeDetailView(
    OrganizationPermissionRequiredMixin,
    View,
):
    required_permission = "employee.view"

    def get(
        self,
        request,
        organization_id,
        employee_id,
    ):

        employee = get_object_or_404(
            Employee.objects
            .select_related(
                "organization",
                "identity",
                "contact",
                "assignment",
                "assignment__department",
                "assignment__position",
                "assignment__job_grade",
                "employment",
            )
            .prefetch_related(
                "documents",
            ),
            id=employee_id,
            organization_id=organization_id,
        )

        return render(
            request,
            "employee/employees/detail.html",
            {
                "employee": employee,
                "organization": employee.organization,
            },
        )

class EmployeeDocumentListView(
    OrganizationPermissionRequiredMixin,
    View,
):
    required_permission = "employee.document.view"

    def get(
        self,
        request,
        organization_id,
        employee_id,
    ):

        employee = get_object_or_404(
            Employee.objects
            .select_related(
                "organization",
                "identity",
            ),
            id=employee_id,
            organization_id=organization_id,
        )

        documents = (
            EmployeeDocument.objects
            .filter(
                employee=employee,
                is_archived=False,
            )
            .order_by(
                "-created_at"
            )
        )

        return render(
            request,
            "employee/documents/list.html",
            {
                "employee": employee,
                "organization": employee.organization,
                "documents": documents,
            },
        )


class EmployeeArchivedDocumentListView(
    OrganizationPermissionRequiredMixin,
    View,
):
    required_permission = "employee.document.view"

    def get(
        self,
        request,
        organization_id,
        employee_id,
    ):

        employee = get_object_or_404(
            Employee,
            id=employee_id,
            organization_id=organization_id,
        )

        documents = (
            EmployeeDocument.objects
            .filter(
                employee=employee,
                is_archived=True,
            )
            .order_by(
                "-updated_at"
            )
        )

        return render(
            request,
            "employee/documents/archived.html",
            {
                "employee": employee,
                "organization": employee.organization,
                "documents": documents,
            },
        )

class EmployeeDocumentUploadView(
    OrganizationPermissionRequiredMixin,
    View,
):
    required_permission = "employee.document.upload"

    def get(
        self,
        request,
        organization_id,
        employee_id,
    ):

        employee = get_object_or_404(
            Employee.objects.select_related(
                "organization",
                "identity",
            ),
            id=employee_id,
            organization_id=organization_id,
        )

        form = EmployeeDocumentUploadForm()

        return render(
            request,
            "employee/documents/upload.html",
            {
                "employee": employee,
                "organization": employee.organization,
                "form": form,
            },
        )

    def post(
        self,
        request,
        organization_id,
        employee_id,
    ):

        employee = get_object_or_404(
            Employee,
            id=employee_id,
            organization_id=organization_id,
        )

        form = EmployeeDocumentUploadForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            document = form.save(
                commit=False
            )

            document.employee = employee

            document = EmployeeDocumentService.create_document(
                employee=employee,
                document_type=document.document_type,
                name=document.name,
                file=document.file,
                description=document.description,
                issue_date=document.issue_date,
                expiry_date=document.expiry_date,
            )

            return redirect(
                "employee:document-list",
                organization_id=organization_id,
                employee_id=employee_id,
            )

        return render(
            request,
            "employee/documents/upload.html",
            {
                "employee": employee,
                "organization": employee.organization,
                "form": form,
            },
        )

class EmployeeEditView(
    OrganizationPermissionRequiredMixin,
    View,
):

    required_permission = "employee.update"

    def get(
        self,
        request,
        organization_id,
        employee_id,
    ):

        employee = get_object_or_404(
            Employee.objects.select_related(
                "organization",
                "identity",
                "contact",
                "employment",
                "assignment",
            ),
            id=employee_id,
            organization=request.organization,
        )

        identity_form = EmployeeIdentityForm(
            instance=employee.identity
        )

        contact_form = EmployeeContactForm(
            instance=employee.contact
        )

        employment_form = EmployeeEmploymentForm(
            instance=employee.employment
        )

        return render(
            request,
            "employee/employees/edit.html",
            {
                "employee": employee,
                "organization": request.organization,
                "identity_form": identity_form,
                "contact_form": contact_form,
                "employment_form": employment_form,
            },
        )

    def post(
        self,
        request,
        organization_id,
        employee_id,
    ):

        employee = get_object_or_404(
            Employee.objects.select_related(
                "organization",
                "identity",
                "contact",
                "employment",
                "assignment",
            ),
            id=employee_id,
            organization=request.organization,
        )

        identity_form = EmployeeIdentityForm(
            request.POST,
            instance=employee.identity,
        )

        contact_form = EmployeeContactForm(
            request.POST,
            instance=employee.contact,
        )

        employment_form = EmployeeEmploymentForm(
            request.POST,
            instance=employee.employment,
        )

        if (
            identity_form.is_valid()
            and contact_form.is_valid()
            and employment_form.is_valid()
        ):

            EmployeeService.update_employee(
                employee=employee,
                identity_data=identity_form.cleaned_data,
                contact_data=contact_form.cleaned_data,
                employment_data=employment_form.cleaned_data,
            )

            return redirect(
                "employee:detail",
                organization_id=organization_id,
                employee_id=employee_id,
            )

        return render(
            request,
            "employee/employees/edit.html",
            {
                "employee": employee,
                "organization": request.organization,
                "identity_form": identity_form,
                "contact_form": contact_form,
                "employment_form": employment_form,
            },
        )