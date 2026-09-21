from django.urls import path

from .views import (
    EmployeeListView,
    EmployeeDetailView,
    EmployeeDocumentListView,
    EmployeeDocumentDetailView,
    EmployeeArchivedDocumentListView,
    EmployeeDocumentRestoreView,
    EmployeeAccountProvisionView,
    EmployeeAccountInviteView,
    EmployeeActivateView,
)

urlpatterns = [

    path(
        "organizations/<uuid:organization_id>/employees/",
        EmployeeListView.as_view(),
        name="employee-list",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/",
        EmployeeDetailView.as_view(),
        name="employee-detail",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/documents/",
        EmployeeDocumentListView.as_view(),
        name="employee-document-list",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/documents/<uuid:document_id>/",
        EmployeeDocumentDetailView.as_view(),
        name="employee-document-detail",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/"
        "<uuid:employee_id>/documents/archived/",
        EmployeeArchivedDocumentListView.as_view(),
        name="employee-archived-document-list",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/"
        "<uuid:employee_id>/documents/<uuid:document_id>/restore/",
        EmployeeDocumentRestoreView.as_view(),
        name="employee-document-restore",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/account/provision/",
        EmployeeAccountProvisionView.as_view(),
        name="employee-account-provision",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/"
        "<uuid:employee_id>/account/invite/",
        EmployeeAccountInviteView.as_view(),
        name="employee-account-invite",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/activate/",
        EmployeeActivateView.as_view(),
        name="employee-activate",
    ),
]

