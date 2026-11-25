# Internal Windows Server deployment preparation

Status: plan and configuration prepared; no server deployment performed.

## Proposed layout

- Windows Server: HTTPS reverse proxy/static frontend hosting, plus Django served by a Windows-compatible WSGI server such as Waitress bound to loopback.
- PostgreSQL: dedicated application database/user, on the server or an internal database host.
- Linux VM: Redis, Celery worker, and one Celery Beat scheduler using the same backend revision and production configuration. Ensure access to PostgreSQL and attendance devices.
- Private employee uploads: persistent storage accessible to the web application; never expose the media directory as a public static location.

Celery does not officially support Windows. A Linux VM is proposed to retain the current task implementation. Confirm VM availability before scheduling deployment; native Windows background execution would require separate implementation and validation.

Sources: [Celery Windows support](https://docs.celeryq.dev/en/stable/faq.html#does-celery-support-windows), [Waitress documentation](https://docs.pylonsproject.org/projects/waitress/en/stable/).

## Values needed from IT

Internal hostname and DNS, HTTPS certificate, PostgreSQL host/credentials, SMTP host and sender account, persistent document/static directories, Linux worker host, service accounts, backup destination/retention, firewall rules, and administrator access. Store actual secrets outside Git with access restricted to service accounts.

## Preparation sequence

1. Review and commit frontend/backend work separately; record both revisions. Remove tracked runtime artifacts from version control as a separate reviewed cleanup.
2. Provision staging services and a least-privilege Windows service account. Install the backend requirements plus the selected WSGI server; pin that server version once selected and validated.
3. Use `backend/.env.production.example` as the configuration reference. Replace all placeholders. The application loads `backend/.env`; the Windows service must explicitly set `DJANGO_SETTINGS_MODULE=config.settings.production` before importing WSGI. Copying the settings-module value into `.env` alone does not select it early enough.
4. Configure trusted proxy handling. `TRUST_PROXY_HTTPS=true` is appropriate only when the proxy strips supplied forwarding headers and sets `X-Forwarded-Proto` itself. Keep the WSGI listener accessible only through that proxy. Otherwise HTTPS redirect loops or spoofed scheme information can occur.
5. Set production frontend `VITE_API_URL` to the real HTTPS API URL and `VITE_ORGANIZATION_ID` to the intended organization UUID, then run `npm ci` and `npm run build`. Host the resulting `frontend/dist/` with SPA fallback. Proxy API/admin/auth paths to Django and serve collected Django static assets separately. Employee documents must remain behind authenticated backend access.
6. Back up existing data, run `manage.py check --deploy --settings=config.settings.production`, `manage.py migrate --settings=config.settings.production`, and `manage.py collectstatic --noinput --settings=config.settings.production`. Plan and test any SQLite-to-PostgreSQL data transfer separately; migrations do not copy existing records.
7. Register the WSGI process with the approved Windows service manager. On the Linux VM, run supervised Celery worker and Beat services with production settings; run exactly one Beat scheduler.
8. Execute the release QA checklist in staging, including invitation email delivery, document access, scheduled tasks, and backup restoration. Validate invitation URLs: APP_BASE_URL must point to a host routing the backend /auth/ paths.
9. Complete deployment review, then switch internal DNS/routing during the agreed maintenance window. Record rollback revisions and preserve a pre-release database/media backup.

## Current limitations

Production settings now require explicit PostgreSQL, SMTP, storage, hosts, and broker configuration and enable HTTPS/secure cookies. Actual connectivity, proxy rules, service registration, backups, and restore procedures require validation on the company infrastructure. Payroll uses full configured amounts without mid-period proration. Frontend role behavior and manual end-to-end QA remain release gates listed in QA_CHECKLIST.md.
