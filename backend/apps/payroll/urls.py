from django.urls import path

from .views import (
    SalaryStructureListView,
    SalaryStructureDetailView,
    EmployeeCompensationListCreateView,
    EmployeePayrollComponentListCreateView,
    PayrollInputListCreateView,
    PayrollProfileListCreateView,
    PayrollApproveView,
    PayrollMarkPaidView,
    PayrollPeriodListCreateView,
    PayrollProcessView,
    PayrollRunListView,
    PayrollRunDetailView,
    OwnPayrollEntryListView,
)

urlpatterns = [
    path("organizations/<uuid:organization_id>/payroll/structures/", SalaryStructureListView.as_view()),
    path("organizations/<uuid:organization_id>/payroll/structures/<uuid:structure_id>/", SalaryStructureDetailView.as_view()),
    path("organizations/<uuid:organization_id>/payroll/periods/", PayrollPeriodListCreateView.as_view()),
    path("organizations/<uuid:organization_id>/payroll/periods/<uuid:period_id>/process/", PayrollProcessView.as_view()),
    path("organizations/<uuid:organization_id>/payroll/compensation/", EmployeeCompensationListCreateView.as_view()),
    path("organizations/<uuid:organization_id>/payroll/components/", EmployeePayrollComponentListCreateView.as_view()),
    path("organizations/<uuid:organization_id>/payroll/profiles/", PayrollProfileListCreateView.as_view()),
    path("organizations/<uuid:organization_id>/payroll/inputs/", PayrollInputListCreateView.as_view()),
    path("organizations/<uuid:organization_id>/payroll/runs/", PayrollRunListView.as_view()),
    path("organizations/<uuid:organization_id>/payroll/runs/<uuid:run_id>/", PayrollRunDetailView.as_view()),
    path("organizations/<uuid:organization_id>/payroll/my-entries/", OwnPayrollEntryListView.as_view()),
    path("organizations/<uuid:organization_id>/payroll/runs/<uuid:run_id>/approve/", PayrollApproveView.as_view()),
    path("organizations/<uuid:organization_id>/payroll/runs/<uuid:run_id>/mark-paid/", PayrollMarkPaidView.as_view()),
]
