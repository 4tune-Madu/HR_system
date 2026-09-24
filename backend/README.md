# HR System Backend Documentation

## 1. Overview

This repository contains a Django-based HR management backend paired with a React frontend. The backend is structured as a modular multi-app Django project and handles user authentication, organization membership, employee records, leave tracking, and access control.

Core stack:

- Python 3.12+
- Django 5.2+
- Django REST Framework
- drf-spectacular for OpenAPI docs
- SQLite for local development
- Celery + Redis-ready configuration
- JWT authentication via Django REST Framework Simple JWT

---

## 2. Project structure

```text
backend/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── celery.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── access/
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── roles.py
│   │   ├── permissions.py
│   │   ├── web_permissions.py
│   │   ├── admin.py
│   │   └── management/commands/
│   ├── accounts/
│   │   ├── models.py
│   │   └── admin.py
│   ├── authentication/
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── urls.py
│   │   ├── web_urls.py
│   │   ├── web_views.py
│   │   └── tests/
│   ├── core/
│   │   ├── models.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── email_service.py
│   │   └── tests.py
│   ├── employee/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── urls.py
│   │   ├── web_urls.py
│   │   ├── web_views.py
│   │   └── tests/
│   ├── leave/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── tasks.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── organization/
│   │   ├── models.py
│   │   ├── views.py
│   │   └── tests.py
│   └── __init__.py
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── dashboard_system_admin.html
│   └── authentication/
├── db.sqlite3
├── manage.py
├── requirements.txt
└── schema.yml
```

---

## 3. App responsibilities

### 3.1 accounts

Handles the custom user model for authentication.

Key file:

- [backend/apps/accounts/models.py](apps/accounts/models.py)

Current model:

- `User`
  - UUID primary key
  - `email` as the username field
  - `first_name`, `last_name`
  - `is_active`, `is_staff`
  - password reset flag
  - custom `UserManager`

Important behavior:

- Django auth is configured with `AUTH_USER_MODEL = 'accounts.user'`
- `email` is the login identifier
- `is_staff` and `is_superuser` are used as system-admin indicators

### 3.2 access

Responsible for organization-level roles and permissions.

Key files:

- [backend/apps/access/models.py](apps/access/models.py)
- [backend/apps/access/services.py](apps/access/services.py)
- [backend/apps/access/roles.py](apps/access/roles.py)
- [backend/apps/access/web_permissions.py](apps/access/web_permissions.py)

Main models:

- `Permission`
- `Role`
- `OrganizationMembership`

Role model behavior:

- each role belongs to an organization
- roles are assigned to users through `OrganizationMembership`
- permissions are attached to roles
- access is enforced via `AccessService.has_permission(...)`

Current system role definitions include:

- `ORGANIZATION_ADMIN`
- `HR_MANAGER`
- `HR_OFFICER`
- `PAYROLL_ADMIN`
- `MANAGER`
- `EMPLOYEE`
- `VIEWER`

The backend is permission-driven: user access is decided from membership + role permissions, not by raw dashboard branching alone.

### 3.3 authentication

Handles API login/logout, JWT flow, and user profile data.

Key files:

- [backend/apps/authentication/urls.py](apps/authentication/urls.py)
- [backend/apps/authentication/views.py](apps/authentication/views.py)
- [backend/apps/authentication/serializers.py](apps/authentication/serializers.py)
- [backend/apps/authentication/web_views.py](apps/authentication/web_views.py)

Endpoints:

- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `POST /api/auth/logout/`
- `GET /api/auth/me/`

Web views:

- `auth/login/`
- `auth/dashboard/`

Current login behavior:

- uses Django `authenticate()` with email + password
- returns JWT access/refresh tokens
- `MeView` returns a limited user profile payload
- the user payload includes role fields such as `is_system_admin`, `is_hr_admin`, `role_code`, and `organization_id` when configured

### 3.4 organization

Represents the company hierarchy and organizational structure.

Key file:

- [backend/apps/organization/models.py](apps/organization/models.py)

Main entities:

- `Organization`
- `Branch`
- `Department`
- `Team`
- `Position`
- `JobGrade`
- `EmploymentType` and related organizational metadata structures

These are the building blocks for HR org design and employee assignment tracking.

### 3.5 employee

This is the primary HR domain in the backend.

Key file:

- [backend/apps/employee/models.py](apps/employee/models.py)

Main models:

- `Employee`
- `EmployeeIdentity`
- `EmployeeContact`
- `EmployeeAssignment`
- `Employment`
- `EmployeeDocument`

Employee relationships include:

- organization
- user account link
- identity data
- contact info
- department/branch/team/position/job grade assignment
- manager linkage
- document attachments

The employee module is the most complete part of the system and is what the current dashboard and employee screens rely on.

### 3.6 leave

Handles leave types, policies, balances, requests, approvals, and accrual logic.

Key file:

- [backend/apps/leave/models.py](models.py)

Main entities:

- `LeaveType`
- `LeavePolicy`
- `LeaveBalance`
- `LeaveRequest`
- `LeaveApproval`
- `LeaveCalendar`
- `LeaveCarryForward` or related accrual records depending on implementation

This module is designed for HR leave management and approval workflows.

### 3.7 core

The general infrastructure app.

Key files:

- [backend/apps/core/urls.py](apps/core/urls.py)
- [backend/apps/core/views.py](apps/core/views.py)
- [backend/apps/core/email_service.py](apps/core/email_service.py)

Responsibilities:

- common app endpoints
- email utilities
- global dashboard/home logic
- shared service support

---

## 4. Data model summary

The backend currently holds these main business entities:

1. User account and login identity
2. Organization and org hierarchy
3. Role and permission assignments
4. Employee master records
5. Employee identity, contact, assignment, and employment details
6. Employee documents
7. Leave policies, balances, and leave cases
8. API access boundaries per organization

---

## 5. Current auth and access model

The access model is built on the following pattern:

- a user belongs to one or more organizations via `OrganizationMembership`
- each membership points to a `Role`
- each role grants a set of permissions
- every protected route verifies the user membership and required permission

In practice, this means:

- system-level admin access is tracked via `is_superuser` / `is_staff`
- organization-level admin access is tracked via role-based membership
- specific pages and actions should be gated using the role/permission system

---

## 6. API surface currently active

The active API routes are centered around authentication and employee management.

### Authentication

- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `POST /api/auth/logout/`
- `GET /api/auth/me/`

### Employees

- `GET /api/employees/organizations/<organization_id>/employees/`
- `POST /api/employees/organizations/<organization_id>/employees/`
- `GET /api/employees/organizations/<organization_id>/employees/<employee_id>/`
- `PATCH /api/employees/organizations/<organization_id>/employees/<employee_id>/`
- `GET /api/employees/organizations/<organization_id>/employees/<employee_id>/documents/`
- `POST /api/employees/organizations/<organization_id>/employees/<employee_id>/documents/`
- `DELETE /api/employees/organizations/<organization_id>/employees/<employee_id>/documents/<document_id>/`
- `GET /api/employees/organizations/<organization_id>/employees/<employee_id>/documents/archived/`
- `POST /api/employees/organizations/<organization_id>/employees/<employee_id>/documents/<document_id>/restore/`

### Web routes

- `auth/login/`
- `auth/dashboard/`
- `employees/...` web pages

---

## 7. Current state and practical notes

This backend is already structurally strong and contains real HR domain logic, but a few important caveats remain:

- the frontend currently relies on a hardcoded or env-provided `VITE_ORGANIZATION_ID`
- role metadata is available through auth payloads, but some parts of the app still assume a single generic dashboard view
- not all model classes are exposed through full REST endpoints yet
- some org-related structures exist in the models but are not yet fully surfaced through API routes in the same way as employee endpoints

---

## 8. Bottom line

The backend currently holds a real HR management system foundation with:

- authentication and permissions
- organization hierarchy
- employee lifecycle data
- leave management support
- document management hooks
- role-based access control

It is not just a stub project; it is a working HR platform skeleton with plenty of domain logic already modeled and partially exposed through APIs.
