# HR System Frontend

React + Vite frontend wired to the Django HR backend.

## Backend endpoints used

- POST `/api/auth/login/`
- POST `/api/auth/refresh/`
- POST `/api/auth/logout/`
- GET `/api/auth/me/`
- GET/POST `/api/employees/organizations/<organization_id>/employees/`
- GET/PATCH/POST `/api/employees/organizations/<organization_id>/employees/<employee_id>/`
- GET/POST `/api/employees/organizations/<organization_id>/employees/<employee_id>/documents/`
- GET/DELETE `/api/employees/organizations/<organization_id>/employees/<employee_id>/documents/<document_id>/`
- GET `/api/employees/organizations/<organization_id>/employees/<employee_id>/documents/archived/`
- POST `/api/employees/organizations/<organization_id>/employees/<employee_id>/documents/<document_id>/restore/`

## Setup

1. `npm install`
2. Copy `.env.example` to `.env`.
3. Set `VITE_API_URL` to the Django API base URL.
4. Set `VITE_ORGANIZATION_ID` to the UUID of the organization the logged-in user belongs to.
5. `npm run dev`

## Important backend note

The backend permission layer determines `request.organization` from the `organization_id` URL and the authenticated user's organization membership. `/api/auth/me/` exposes active organization memberships, roles, and permissions. The frontend currently selects the organization through `VITE_ORGANIZATION_ID`.

Organization structure endpoints are wired under `/api/organization/`. Leave, attendance, payroll, and onboarding endpoints are also wired into `backend/config/urls.py`. The main development frontend lives in the parent checkout's `frontend/` directory; this checkout also contains a frontend copy.

## Payroll effective dates

Processing excludes compensation, allowances, and deductions whose `effective_from` date falls after the payroll period's end date. Records effective on the end date are included. The current calculation uses full configured amounts and does not prorate mid-period changes.

Run payroll regression tests from `backend/`:

```powershell
& .\.venv\Scripts\python.exe manage.py test apps.payroll.tests
```
