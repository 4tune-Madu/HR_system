from django.urls import path
from . import web_views
from .web_views import (
    EmployeeListView,
    EmployeeDocumentListView,
)


app_name = "employee"


urlpatterns = [

    # Employee
    path(
        "organizations/<uuid:organization_id>/employees/",
        web_views.EmployeeListView.as_view(),
        name="list",
    ),
    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/",
        web_views.EmployeeDetailView.as_view(),
        name="detail",
    ),

    # Employee Documents
    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/documents/",
        web_views.EmployeeDocumentListView.as_view(),
        name="document-list",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/documents/archived/",
        web_views.EmployeeArchivedDocumentListView.as_view(),
        name="document-archived",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/documents/upload/",
        web_views.EmployeeDocumentUploadView.as_view(),
        name="document-upload",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/edit/",
        web_views.EmployeeEditView.as_view(),
        name="edit",
    ),

]