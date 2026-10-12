from django.urls import path

from .views import (
    LeaveRequestListView,
    LeaveRequestDetailView,
    LeaveRequestSubmitView,
    LeaveRequestApproveView,
    LeaveRequestRejectView,
    LeaveRequestCancelView,

    LeaveTypeListView,
    LeaveTypeDetailView,
    LeaveTypeActivateView,
    LeaveTypeDeactivateView,

    LeavePolicyListView,
    LeavePolicyDetailView,
    LeavePolicyActivateView,
    LeavePolicyDeactivateView,

    LeaveBalanceListView,
    LeaveBalanceDetailView,
    EmployeeLeaveBalanceListView,

    PublicHolidayActivateView,
    PublicHolidayDeactivateView,
    PublicHolidayDetailView,
    PublicHolidayListView,
    
    WorkScheduleActivateView,
    WorkScheduleDeactivateView,
    WorkScheduleDetailView,
    WorkScheduleListView,
    WorkScheduleSetDefaultView,

    EmployeeWorkScheduleListView,
    EmployeeWorkScheduleDetailView,
    EmployeeWorkScheduleActivateView,
    EmployeeWorkScheduleDeactivateView,

    EmployeeLeaveEntitlementDetailView,
    EmployeeLeaveEntitlementListView,

    LeaveBalanceAdjustmentListView,

    LeaveAccrualListView,

    LeaveApprovalRuleListView,
    LeaveApprovalRuleDetailView,
    LeaveApprovalRuleActivateView,
    LeaveApprovalRuleDeactivateView,
)


urlpatterns = [

    # -----------------------------------
    # Leave Requests
    # -----------------------------------

    path(
        "organizations/<uuid:organization_id>/leave/requests/",
        LeaveRequestListView.as_view(),
        name="leave-request-list",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/requests/<uuid:request_id>/",
        LeaveRequestDetailView.as_view(),
        name="leave-request-detail",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/requests/<uuid:request_id>/submit/",
        LeaveRequestSubmitView.as_view(),
        name="leave-request-submit",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/requests/<uuid:request_id>/approve/",
        LeaveRequestApproveView.as_view(),
        name="leave-request-approve",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/requests/<uuid:request_id>/reject/",
        LeaveRequestRejectView.as_view(),
        name="leave-request-reject",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/requests/<uuid:request_id>/cancel/",
        LeaveRequestCancelView.as_view(),
        name="leave-request-cancel",
    ),

    # -----------------------------------
    # Leave Types
    # -----------------------------------

    path(
        "organizations/<uuid:organization_id>/leave/types/",
        LeaveTypeListView.as_view(),
        name="leave-type-list",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/types/<uuid:leave_type_id>/",
        LeaveTypeDetailView.as_view(),
        name="leave-type-detail",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/types/<uuid:leave_type_id>/activate/",
        LeaveTypeActivateView.as_view(),
        name="leave-type-activate",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/types/<uuid:leave_type_id>/deactivate/",
        LeaveTypeDeactivateView.as_view(),
        name="leave-type-deactivate",
    ),

    # -----------------------------------
    # Leave Policies
    # -----------------------------------

    path(
        "organizations/<uuid:organization_id>/leave/policies/",
        LeavePolicyListView.as_view(),
        name="leave-policy-list",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/policies/<uuid:policy_id>/",
        LeavePolicyDetailView.as_view(),
        name="leave-policy-detail",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/policies/<uuid:policy_id>/activate/",
        LeavePolicyActivateView.as_view(),
        name="leave-policy-activate",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/policies/<uuid:policy_id>/deactivate/",
        LeavePolicyDeactivateView.as_view(),
        name="leave-policy-deactivate",
    ),


    # -----------------------------------
    # Leave Balance
    # -----------------------------------

    path(
        "organizations/<uuid:organization_id>/leave/balances/",
        LeaveBalanceListView.as_view(),
        name="leave-balance-list",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/balances/<uuid:balance_id>/",
        LeaveBalanceDetailView.as_view(),
        name="leave-balance-detail",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/leave/balances/",
        EmployeeLeaveBalanceListView.as_view(),
        name="employee-leave-balance-list",
    ),

    # -----------------------------------
    # Work Schedules
    # -----------------------------------

    path(
        "organizations/<uuid:organization_id>/leave/work-schedules/",
        WorkScheduleListView.as_view(),
        name="work-schedule-list",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/work-schedules/<uuid:schedule_id>/",
        WorkScheduleDetailView.as_view(),
        name="work-schedule-detail",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/work-schedules/<uuid:schedule_id>/activate/",
        WorkScheduleActivateView.as_view(),
        name="work-schedule-activate",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/work-schedules/<uuid:schedule_id>/deactivate/",
        WorkScheduleDeactivateView.as_view(),
        name="work-schedule-deactivate",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/work-schedules/<uuid:schedule_id>/set-default/",
        WorkScheduleSetDefaultView.as_view(),
        name="work-schedule-set-default",
    ),

    # -----------------------------------
    # Public Holidays
    # -----------------------------------

    path(
        "organizations/<uuid:organization_id>/leave/holidays/",
        PublicHolidayListView.as_view(),
        name="public-holiday-list",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/holidays/<uuid:holiday_id>/",
        PublicHolidayDetailView.as_view(),
        name="public-holiday-detail",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/holidays/<uuid:holiday_id>/activate/",
        PublicHolidayActivateView.as_view(),
        name="public-holiday-activate",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/holidays/<uuid:holiday_id>/deactivate/",
        PublicHolidayDeactivateView.as_view(),
        name="public-holiday-deactivate",
    ),

    # -----------------------------------
    # Employee Work Schedule
    # -----------------------------------

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/leave/work-schedules/",
        EmployeeWorkScheduleListView.as_view(),
        name="employee-work-schedule-list",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/leave/work-schedules/<uuid:assignment_id>/",
        EmployeeWorkScheduleDetailView.as_view(),
        name="employee-work-schedule-detail",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/leave/work-schedules/<uuid:assignment_id>/activate/",
        EmployeeWorkScheduleActivateView.as_view(),
        name="employee-work-schedule-activate",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/leave/work-schedules/<uuid:assignment_id>/deactivate/",
        EmployeeWorkScheduleDeactivateView.as_view(),
        name="employee-work-schedule-deactivate",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/leave/entitlements/",
        EmployeeLeaveEntitlementListView.as_view(),
        name="employee-leave-entitlement-list",
    ),

    path(
        "organizations/<uuid:organization_id>/employees/<uuid:employee_id>/leave/entitlements/<uuid:entitlement_id>/",
        EmployeeLeaveEntitlementDetailView.as_view(),
        name="employee-leave-entitlement-detail",
    ),

    # -----------------------------------
    # Leave Adjumenent
    # -----------------------------------

    path(
        "organizations/<uuid:organization_id>/leave/balances/<uuid:balance_id>/adjustments/",
        LeaveBalanceAdjustmentListView.as_view(),
        name="leave-balance-adjustment-list",
    ),

    # -----------------------------------
    # Leave Accrual
    # -----------------------------------

    path(
        "organizations/<uuid:organization_id>/leave/balances/<uuid:balance_id>/accruals/",
        LeaveAccrualListView.as_view(),
        name="leave-accrual-list",
    ),

    # -----------------------------------
    # Leave Approval Rules
    # -----------------------------------

    path(
        "organizations/<uuid:organization_id>/leave/approval-rules/",
        LeaveApprovalRuleListView.as_view(),
        name="leave-approval-rule-list",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/approval-rules/<uuid:rule_id>/",
        LeaveApprovalRuleDetailView.as_view(),
        name="leave-approval-rule-detail",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/approval-rules/<uuid:rule_id>/activate/",
        LeaveApprovalRuleActivateView.as_view(),
        name="leave-approval-rule-activate",
    ),

    path(
        "organizations/<uuid:organization_id>/leave/approval-rules/<uuid:rule_id>/deactivate/",
        LeaveApprovalRuleDeactivateView.as_view(),
        name="leave-approval-rule-deactivate",
    ),
]