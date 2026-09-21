ROLE_PERMISSIONS = {
    "ORGANIZATION_ADMIN": [
        "organization.view",
        "organization.update",

        "employee.view",
        "employee.create",
        "employee.update",
        "employee.deactivate",
        "employee.activate",

        "employee.account.provision",
        "employee.account.invite",   

        "employee.document.view",
        "employee.document.upload",
        "employee.document.archive",
        "employee.document.restore",

        "leave.view",
        "leave.request",
        "leave.approve",
        "leave.manage",

        "attendance.view",

        "payroll.view",
        "payroll.process",
        "payroll.approve",
        "payroll.view_own",
    ],


    "HR_MANAGER": [
        "organization.view",

        "employee.view",
        "employee.create",
        "employee.update",
        "employee.deactivate",

        "employee.account.provision",

        "employee.document.view",
        "employee.document.upload",
        "employee.document.upload",
        "employee.document.restore",

        "leave.view",
        "leave.request",
        "leave.approve",

        "attendance.view",

        "payroll.view",
        "payroll.view_own",

    ],

    "HR_OFFICER": [
        "organization.view",

        "employee.view",
        "employee.create",
        "employee.update",

        "employee.account.provision",

        "employee.document.view",
        "employee.document.upload",

        "leave.view",
        "leave.request",

        "attendance.view",
    ],

    "PAYROLL_ADMIN": [
        "employee.view",

        "payroll.view",
        "payroll.process",
        "payroll.approve",
    ],

    "MANAGER": [
        "employee.view",

        "leave.view",
        "leave.approve",

        "attendance.view",
    ],

    "EMPLOYEE": [
        "employee.view_own",
        "employee.update_own",

        "employee.document.view",

        "leave.view",
        "leave.request",

        "payroll.view_own",
    ],

    "VIEWER": [
        "organization.view",
        "employee.view",
        "employee.document.view",
        "leave.view",
        "attendance.view",
        "payroll.view",
    ],
}