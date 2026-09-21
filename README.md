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

The backend permission layer determines `request.organization` from the `organization_id` URL and the authenticated user's organization membership. The current `/api/auth/me/` response does not expose organization membership, so the frontend currently uses `VITE_ORGANIZATION_ID`.

The organization models exist, but REST endpoints for creating/listing branches, departments, teams, positions and job grades are not currently wired into `config/urls.py`. The employee form therefore uses UUID fields for those relationships for now.
