# BT Technologies HR System

Internal HR and workforce-management software for BT Technologies. The system currently contains a React/Vite frontend and a Django REST Framework backend. It supports organization structure, employee records, documents, leave, attendance, payroll, onboarding, authentication, and organization-scoped role-based access control (RBAC).

Recruitment, ATS, public-facing features, and mobile applications are outside the scope of this repository unless a future project brief adds them.

## Start here

| If you are... | Read first |
| --- | --- |
| Starting the whole application | [Local setup and verification](docs/LOCAL_SETUP.md) |
| Working on the frontend | [Frontend guide](#frontend-guide) |
| Working on Django or the API | [Backend/Django guide](#backenddjango-guide) |
| Adding or changing an endpoint | [API conventions](#api-conventions) and [Django request flow](#django-request-flow) |
| Troubleshooting local startup | [Troubleshooting](#troubleshooting) |

## Repository layout

```text
HR_system/
├── frontend/                         React 19 + Vite application
│   ├── src/api/                      API client modules
│   ├── src/components/               Shared UI and route guards
│   ├── src/context/                  React context, including authentication
│   └── src/pages/                    Feature pages
├── HR_system-backend-runtime/
│   └── backend/                      Django project root
│       ├── apps/                     Django applications
│       ├── config/                   Settings, URLs, WSGI/ASGI/Celery config
│       ├── templates/                Server-rendered Django templates
│       ├── manage.py                 Django command entry point
│       ├── requirements.txt          Python dependencies
│       └── schema.yml                Generated/checked API schema
├── docs/                             Operational notes and local QA information
└── .gitignore
```

`HR_system-backend-runtime` is itself a Git checkout. Keep backend changes in that checkout and frontend/root changes in the parent checkout. The project has historically used `frontend-dev` and `backend-dev` branches; confirm the active branch before editing or committing.

## Technology summary

### Frontend

- React 19, React Router 7, Vite 7, and `lucide-react`.
- The dev server is fixed to `127.0.0.1:5174`. Port 5173 is used by another local project.
- API calls use `fetch` through [`frontend/src/api/client.js`](frontend/src/api/client.js). The client adds JWT headers, refreshes expired access tokens once, handles JSON and file responses, and follows safe same-origin pagination links.
- Access and refresh tokens are stored in browser `localStorage` under `access` and `refresh`.

### Backend

- Django 5.2, Django REST Framework, SimpleJWT, `django-filter`, and drf-spectacular.
- SQLite is the default local database. Production settings can select a different database and infrastructure.
- Celery and Redis are configured for background leave and attendance tasks, but are not required for the basic local API server.
- The default API base is `http://127.0.0.1:8000/api`.

## Local setup

For the current machine-specific verification notes, see [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md). The short version is:

### 1. Backend terminal

```powershell
cd HR_system-backend-runtime/backend

# Existing environment in this checkout:
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Configure local secrets once. Do not commit .env.
Copy-Item .env.example .env

& .\.venv\Scripts\python.exe manage.py migrate
& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --settings=config.settings.development
```

If the virtual environment does not exist, create it with `py -m venv .venv`, activate it, and install `requirements.txt`. A local `SECRET_KEY` is required; copy `.env.example` and replace the placeholder value.

### 2. Frontend terminal

```powershell
cd frontend
Copy-Item .env.example .env       # first run only
npm install
npm run dev
```

The frontend opens at `http://127.0.0.1:5174`. Set `VITE_API_URL` to the backend API base and `VITE_ORGANIZATION_ID` to an organization UUID the signed-in user can access.

### Environment variables

Frontend [`frontend/.env.example`](frontend/.env.example):

```dotenv
VITE_API_URL=http://127.0.0.1:8000/api
VITE_ORGANIZATION_ID=replace-with-organization-uuid
```

Backend [`HR_system-backend-runtime/backend/.env.example`](HR_system-backend-runtime/backend/.env.example):

```dotenv
SECRET_KEY=replace-with-a-long-random-secret
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
```

Never commit `.env`, real JWTs, database files, employee documents, production secrets, or generated credentials.

## Frontend guide

### Application flow

The entry point is [`frontend/src/main.jsx`](frontend/src/main.jsx), which renders [`frontend/src/App.jsx`](frontend/src/App.jsx). `App.jsx` establishes the router and wraps routes with `AuthProvider`. Authenticated routes pass through `ProtectedRoute`; feature routes can additionally pass through `PermissionRoute`.

The main authenticated layout is [`frontend/src/components/Layout.jsx`](frontend/src/components/Layout.jsx). Add a new page by:

1. Creating the page in `frontend/src/pages/`.
2. Adding its route in `App.jsx`.
3. Applying the smallest appropriate permission guard.
4. Adding or extending an API module in `frontend/src/api/`.
5. Adding navigation in `Layout.jsx` if the page should appear in the sidebar.
6. Keeping reusable controls in `frontend/src/components/` rather than duplicating them in pages.

### Frontend routes

| Route | Page | Guard |
| --- | --- | --- |
| `/login` | Login | Public |
| `/dashboard` | Dashboard | Authenticated |
| `/profile` | My profile | Authenticated |
| `/employees`, `/employees/:id` | Employee list/details | `employee.view` |
| `/employees/new` | Create employee | `employee.create` |
| `/employees/:id/edit` | Edit employee | `employee.update` |
| `/employees/:id/documents`, `/documents` | Documents | `employee.document.view` |
| `/onboarding` | Onboarding tasks | `employee.view` |
| `/leave-management` | Leave | `leave.view` |
| `/attendance` | Attendance | `attendance.view` |
| `/payroll` | Payroll | `payroll.view` |
| `/organization` | Organization structure | `organization.structure.manage` |
| `/settings` | Settings | Authenticated |

### API modules

Keep feature requests in the matching module:

- `auth.js`: login, logout, refresh, and current-user requests.
- `employees.js`: employees, employee documents, activation, account provisioning, and invitations.
- `organization.js`: branches, departments, teams, job grades, positions, and attendance settings.
- `leave.js`: requests, types, policies, balances, holidays, schedules, and approval rules.
- `attendance.js`: devices, mappings, records, sync, check-in, and reconciliation.
- `payroll.js`: salary structures, periods, runs, compensation, components, inputs, and employee entries.
- `onboarding.js`: onboarding task list/create/update.

Use `api('/path/', options)` instead of calling `fetch` directly. Use `listAll()` when the UI needs every page of a paginated collection. Use `FormData` for uploads; the shared client deliberately does not set `Content-Type: application/json` for `FormData`.

When adding a request:

- Keep the path relative to `VITE_API_URL`, including the leading slash.
- Use `JSON.stringify(payload)` for JSON bodies.
- Use `PATCH` for partial updates, `POST` for commands/actions, and `DELETE` for removal/archive operations according to the backend route.
- Surface API errors through the shared `Error` message so users see field-level validation where available.
- Do not hard-code an organization UUID. Read it from the shared `VITE_ORGANIZATION_ID` configuration pattern used by existing API modules.

## Backend/Django guide

### How to navigate Django

Always run Django commands from `HR_system-backend-runtime/backend`, because that directory contains `manage.py`, `config/`, `apps/`, and the database.

The usual path for an API request is:

```text
config/urls.py
  -> apps/<feature>/urls.py
  -> apps/<feature>/views.py
  -> apps/<feature>/serializers.py
  -> apps/<feature>/models.py
  -> apps/<feature>/services.py (business rules/integrations where present)
```

Permissions and organization isolation are part of that flow. Before querying or mutating data, check how the existing view obtains `organization_id`, authenticates the user, and applies the feature permission. Do not bypass those checks by using an unscoped queryset.

### Django project files

- [`manage.py`](HR_system-backend-runtime/backend/manage.py): command-line entry point; defaults to development settings.
- [`config/urls.py`](HR_system-backend-runtime/backend/config/urls.py): top-level routing, admin, API documentation, and server-rendered web routes.
- `config/settings/base.py`: shared installed apps, middleware, REST framework defaults, JWT, CORS, email, and Celery settings.
- `config/settings/development.py`: local development overrides.
- `config/settings/production.py`: production-oriented overrides; review before deployment.
- `apps/accounts/`: custom `User` model and account-related behavior. `AUTH_USER_MODEL` is `accounts.user`.
- `apps/access/`: roles, permissions, organization membership, and permission helpers.
- `apps/authentication/`: JWT login/logout/refresh, `/me/`, password setup, and auth services.
- `apps/core/`: shared home page and core services.

### Feature app responsibilities

| App | Responsibility |
| --- | --- |
| `organization` | Branches, departments, teams, job grades, positions, and attendance settings |
| `employee` | Employee records, lifecycle actions, documents, account provisioning, and invitations |
| `leave` | Leave requests, policies, balances, accruals, holidays, schedules, and approval rules |
| `attendance` | Devices, device users/mappings, events, records, sync, check-in, and reconciliation |
| `payroll` | Salary structures, compensation, payroll components, periods, runs, approval, and payment status |
| `onboarding` | Employee onboarding tasks |

Most feature apps contain `models.py`, `serializers.py`, `views.py`, and `urls.py`; leave and attendance also contain asynchronous `tasks.py`. Tests live in each app's `tests/` directory or adjacent test modules.

### Adding or changing a Django feature

1. Find the owning app; do not create a second app for an existing domain.
2. Update the model and add a migration with `makemigrations`.
3. Put validation and representation in serializers/forms as appropriate.
4. Put reusable domain rules in `services.py` when the logic is used by more than one view or task.
5. Add the view and route under the existing organization URL convention.
6. Apply authentication, organization membership, and feature permission checks.
7. Add tests for success, validation failures, forbidden access, and cross-organization isolation.
8. Update the frontend API module and page if the endpoint is user-facing.
9. Run `check`, targeted tests, the full backend suite, and schema generation/inspection.

Do not edit an existing migration that has already been shared. Create a new migration instead. Do not put business rules in `config/urls.py` or in React components.

## API conventions

### Base URLs and authentication

- API base: `http://127.0.0.1:8000/api/` locally.
- Login: `POST /api/auth/login/` with the user's email and password.
- Refresh: `POST /api/auth/refresh/` with the refresh token.
- Current user: `GET /api/auth/me/`.
- Logout: `POST /api/auth/logout/` with the refresh token.
- Protected requests use `Authorization: Bearer <access-token>`.

Access tokens last 30 minutes; refresh tokens last one day and rotate with blacklist support. A 401 causes the frontend client to attempt one refresh, then clears tokens and requires login again.

### Organization-scoped paths

Most business endpoints follow this shape:

```text
/api/<domain>/organizations/<organization_id>/<resource>/
```

Examples:

```text
GET   /api/employees/organizations/<org-id>/employees/
GET   /api/leave/organizations/<org-id>/leave/requests/
GET   /api/attendance/organizations/<org-id>/attendance/records/
GET   /api/payroll/organizations/<org-id>/payroll/runs/
GET   /api/onboarding/organizations/<org-id>/onboarding/tasks/
GET   /api/organization/<org-id>/departments/
```

Action endpoints use a trailing verb such as `/submit/`, `/approve/`, `/activate/`, `/restore/`, `/process/`, `/sync/`, or `/reconcile/`. Preserve the trailing slash convention because Django URL patterns use it.

### Pagination and schema

DRF uses page-number pagination with a default page size of 20. A list response normally has `count`, `next`, `previous`, and `results`. The frontend `listAll()` helper follows all pages when it needs a complete list.

Interactive API documentation is available while Django is running:

- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
- Django admin: `http://127.0.0.1:8000/admin/`

Use the schema to confirm request and response fields before wiring a new frontend form. Treat server-side validation and permissions as authoritative; frontend guards are only a usability layer.

## Important domain rules

- Every organization-scoped request must be isolated to the authenticated user's organization membership and permission set.
- The frontend currently selects one organization through `VITE_ORGANIZATION_ID`; `/api/auth/me/` exposes memberships, roles, and permissions.
- Employee documents are protected by organization and employee access checks. Downloads return file responses, not JSON.
- Payroll processing includes compensation, allowances, and deductions effective on or before the payroll period end date. The current implementation uses full configured amounts and does not prorate mid-period changes.
- Leave workflows require configured leave types, policies, balances/entitlements, schedules, and an employee profile for the requester.
- Device-based attendance synchronization requires a reachable, configured device. Manual check-in is available for local testing.
- Local email uses Django's in-memory email backend, so invitation emails do not arrive in a real inbox during development.

## Background workers

Celery schedules are defined in the backend settings. Current scheduled work includes monthly leave accrual, yearly balance initialization, leave reconciliation, morning/noon/evening attendance synchronization, and nightly attendance reconciliation.

For local worker testing, start Redis and run from the backend directory:

```powershell
& .\.venv\Scripts\celery.exe -A config worker --loglevel=INFO
& .\.venv\Scripts\celery.exe -A config beat --loglevel=INFO
```

If the environment does not expose `celery.exe`, use `& .\.venv\Scripts\python.exe -m celery ...`. The API itself can run without a worker, but scheduled or queued work will not execute.

## Validation commands

From `HR_system-backend-runtime/backend`:

```powershell
& .\.venv\Scripts\python.exe manage.py check
& .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
& .\.venv\Scripts\python.exe manage.py test
```

Run a focused backend test while iterating:

```powershell
& .\.venv\Scripts\python.exe manage.py test apps.payroll.tests
& .\.venv\Scripts\python.exe manage.py test apps.employee.tests
```

From `frontend`:

```powershell
npm test
npm run build
```

The current documented baseline is 368 passing backend tests, six document-download regression tests, 14 targeted organization/access tests, five frontend API tests, and a passing production build. Re-run the suite after changes; do not assume those historical counts remain unchanged.

## Git and collaboration workflow

1. Check `git status --short --branch` in the parent and in `HR_system-backend-runtime` before editing.
2. Keep frontend changes in the parent frontend checkout and backend changes in the nested backend checkout.
3. Make small, domain-focused commits. Include migrations with the backend change that requires them.
4. Never commit local `.env` files, `db.sqlite3`, generated `dist/`, uploaded employee documents, logs, or tokens.
5. Before handing off, report changed files, migrations, validation commands, and any external services still required.

## Troubleshooting

### Frontend cannot connect to the API

Confirm Django is running on port 8000, `frontend/.env` points to `http://127.0.0.1:8000/api`, and the browser origin is one of the CORS/CSRF origins in the development settings. Restart Vite after changing `.env`.

### Port 5174 is busy

Use the existing HR frontend if it is already running. Do not stop unrelated applications just to free a port. The fixed port is intentional so the frontend does not silently move to a different origin.

### The API returns 401

Log in again, inspect `/api/auth/me/`, and verify the user has an active organization membership. If the problem is permission-specific, check the relevant permission rather than weakening the route guard or backend permission.

### A list looks incomplete

The API is paginated at 20 records per page. Use `listAll()` for dropdowns and complete reference lists, or explicitly handle `next`/`results` in the page.

### A leave or attendance workflow fails

Check its prerequisites first: organization configuration, employee profile, leave types/policies/balances, work schedules, or a reachable attendance device. The local limitations and verified workflows are recorded in [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md).

### Migration or import errors

Run commands from `HR_system-backend-runtime/backend`, ensure the correct `.venv` is being used, run `manage.py check`, and inspect the app's migrations. Do not delete the database or migration files as a first response.

## Current scope and follow-up work

- Complete manual end-to-end QA against a running backend and configured organization.
- Add broader frontend automated tests.
- Replace development deployment settings with managed database, email provider, secret management, allowed hosts, CORS, static/media storage, and Redis/Celery configuration.
- Keep frontend and backend changes reviewed and committed separately where the nested checkout requires it.
