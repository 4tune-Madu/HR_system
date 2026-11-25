# HR system release QA

Status: manual checks pending. Automated test success does not mark these complete.
Use a staging organization and synthetic employee/payroll data.

## Access and accounts

- [ ] Test organization admin, HR manager, HR officer, payroll admin, manager, employee, and viewer accounts.
- [ ] Confirm each role can access only its permitted pages and API operations.
- [ ] Confirm an account in organization A cannot read or modify organization B.
- [ ] Verify login, token expiry/refresh, logout, invitation delivery, and password setup.
- [ ] Verify system-admin behavior against backend membership permissions; frontend currently bypasses route checks for system admins, while backend requires membership permissions.
- [ ] Verify employee dashboard behavior; it currently requests the employee directory, which requires employee.view.

## HR workflows

- [ ] Create organization structure, create an employee, edit assignment, deactivate/reactivate.
- [ ] Upload, download, archive, and restore employee documents; verify private access.
- [ ] Configure leave policies, balances, holidays, schedules; request, approve/reject, and cancel leave.
- [ ] Check attendance manually, synchronize a test device, map employees, reconcile open records.
- [ ] Create onboarding tasks, assign them, and complete them.

## Payroll

- [ ] Configure compensation and allowances/deductions, process a period, inspect totals, approve, and mark paid.
- [ ] Verify future-dated compensation/components are excluded from earlier periods.
- [ ] Confirm the business accepts the current full-amount calculation; mid-period proration is not implemented.
- [ ] Verify only payroll.approve users see working approval/payment actions; frontend currently displays these to payroll processors too.
- [ ] Verify employees see only their own approved/paid entries.

## Operations

- [ ] Test production environment validation, HTTPS/proxy configuration, and frontend API URL.
- [ ] Verify SMTP delivery and Celery worker/Beat execution.
- [ ] Restart server and confirm services recover automatically.
- [ ] Back up and restore database and private documents in a separate environment.
- [ ] Validate attendance-device connectivity from the worker host.
- [ ] Record approver, date, build revision, and evidence for completed checks.
