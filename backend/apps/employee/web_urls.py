from django.urls import path
from . import web_views
from .web_views import (
    EmployeeListView
)


app_name = "employee"


urlpatterns = [

    path(
        "organizations/<uuid:organization_id>/employees/",
        web_views.EmployeeListView.as_view(),
        name="list",
    ),

]