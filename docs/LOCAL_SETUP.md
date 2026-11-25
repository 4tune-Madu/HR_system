# Run HR on this computer

HR frontend: http://127.0.0.1:5174

HR API: http://127.0.0.1:8000/api/

Port 5173 is used by the separate Ekotix project. HR uses a fixed port of 5174 so a conflict is reported instead of silently moving to another address.

## Start the backend

Open PowerShell in the project root:

```powershell
cd HR_system-backend-runtime/backend
& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --settings=config.settings.development
```

## Start the frontend

Open a second PowerShell window in the project root:

```powershell
cd frontend
npm run dev
```

Keep both terminals open. Stop each service with Ctrl+C in its terminal. If a port is already occupied by HR, use the existing service rather than starting another copy. Do not stop unrelated applications to free ports.

The existing frontend `.env` selects the local API and organization. The backend `.env` contains the local secret key. These files must remain untracked. No deployment configuration is required for local use.

## Local verification on 2026-10-13

- Existing HR demo account signed in successfully.
- Employee created and edited through the browser; assignment lookup permission errors fixed.
- Onboarding task created with no due date and completed through the browser.
- Manual attendance check-in saved and appeared in the attendance table.
- Synthetic payroll compensation configured, period created, processed, and approved; gross/net totals both matched 100000.00 with no deductions.
- Authenticated document-download endpoint: original file bytes, access denial, employee/organization isolation, and missing-file behavior covered by six passing regression tests.
- Synthetic employee document uploaded and downloaded through the browser; downloaded content checked against the original fixture.
- Dashboard, leave, payroll, onboarding, attendance, and employee screens loaded.
- Backend baseline suite: 368 passing tests before these additional changes.
- Targeted organization/access tests: 14 passing; document-download tests: 6 passing.
- Frontend API tests: 5 passing; production build passed.

Synthetic records are clearly named `Local QA Test Employee` and `Local QA: verify onboarding`. They are test fixtures, not actual staff records.

## Still needing local workflow validation

Leave request/approval requires leave types, policies, balances, and an employee profile linked to the requester; the current HR demo account has no employee profile. Physical attendance-device synchronization requires a reachable configured device. Outgoing invitations use the current in-memory development email backend, so they do not arrive in an inbox. These prerequisites must be configured before those workflows can be called fully verified.

## Starter dropdown options

The local organization now has 5 starter branches, 11 departments, 13 teams, 32 positions, 8 job grades, and 7 leave types. These are editable sample options for local use, not a statement of BT Technologies' official organization or leave policy. Existing records are preserved.

Manager choices use existing employee records; no fictional managers, attendance devices, salaries, leave entitlements, or public holidays are added by the options setup. Gender now has a dropdown with an optional unspecified choice and preserves existing custom values. Organization dropdowns fetch every API page.

To restore missing starter choices without duplicating or replacing existing ones, run from the backend directory:

```powershell
& .\.venv\Scripts\python.exe manage.py seed_local_options --organization 39b25512-6c42-455f-83d3-0469711acaaa
```

## Tests

From `frontend/`, run `npm test` and `npm run build`.

From `HR_system-backend-runtime/backend/`, run `& .\.venv\Scripts\python.exe manage.py test`.
