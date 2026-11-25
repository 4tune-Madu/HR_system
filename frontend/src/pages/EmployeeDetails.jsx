import React, {useCallback, useEffect, useState} from 'react';
import {Link, useParams} from 'react-router-dom';
import {ArrowLeft, Edit3, FileText, Mail, MapPin, Phone, UserCheck, UserPlus, UserX} from 'lucide-react';
import {activateEmployee, deactivateEmployee, getEmployee, inviteEmployeeAccount, provisionEmployeeAccount} from '../api/employees';
import {useAuth} from '../context/AuthContext';

const displayName = employee => [employee.identity?.first_name, employee.identity?.middle_name, employee.identity?.last_name].filter(Boolean).join(' ') || 'Unnamed employee';

export default function EmployeeDetails() {
  const {id} = useParams();
  const {user} = useAuth();
  const [employee, setEmployee] = useState(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const membership = user?.memberships?.find((item) => item.organization_id === import.meta.env.VITE_ORGANIZATION_ID);
  const permissions = membership?.permissions || [];
  const has = (permission) => user?.is_system_admin || permissions.includes(permission);
  const canEdit = has('employee.update');
  const canDeactivate = has('employee.deactivate');
  const canActivate = has('employee.activate');
  const canProvision = has('employee.account.provision');
  const canInvite = has('employee.account.invite');
  const canViewDocuments = has('employee.document.view');

  const loadEmployee = useCallback(async () => {
    setError('');
    try {
      setEmployee(await getEmployee(id));
    } catch (requestError) {
      setError(requestError.message);
    }
  }, [id]);

  useEffect(() => { loadEmployee(); }, [loadEmployee]);

  const runAction = async (action, successMessage) => {
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const result = await action();
      if (result?.id) setEmployee(result);
      else await loadEmployee();
      setMessage(successMessage);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  if (error && !employee) return <div className="error banner" role="alert">{error}</div>;
  if (!employee) return <div className="loading">Loading employee…</div>;

  const contact = employee.contact || {};
  const identity = employee.identity || {};
  const assignment = employee.assignment || {};
  const employment = employee.employment || {};

  return <div>
    <Link className="back" to="/employees"><ArrowLeft size={17}/> Employees</Link>
    <div className="profile-hero">
      <div className="big-avatar">{identity.first_name?.[0]}{identity.last_name?.[0]}</div>
      <div className="profile-identity"><span className="eyebrow">Employee profile</span><h2>{displayName(employee)}</h2><p>{assignment.position_name || 'Position not assigned'} · {assignment.department_name || 'Department not assigned'}</p></div>
      <div className="profile-actions">
        <span className={employee.is_active ? 'status active' : 'status inactive'}>{employee.is_active ? 'Active' : 'Inactive'}</span>
        {canEdit && <Link className="link-button" to={`/employees/${id}/edit`}><Edit3 size={16}/> Edit</Link>}
        {canViewDocuments && <Link className="link-button" to={`/employees/${id}/documents`}><FileText size={16}/> Documents</Link>}
        {employee.is_active && canDeactivate && <button className="link-button" type="button" disabled={busy} onClick={() => window.confirm(`Deactivate ${displayName(employee)}?`) && runAction(() => deactivateEmployee(id), 'Employee deactivated.')}><UserX size={16}/> Deactivate</button>}
        {!employee.is_active && canActivate && <button className="link-button" type="button" disabled={busy} onClick={() => runAction(() => activateEmployee(id), 'Employee activated.')}><UserCheck size={16}/> Activate</button>}
      </div>
    </div>
    {error && <div className="error banner" role="alert">{error}</div>}
    {message && <div className="success banner" role="status">{message}</div>}
    <section className="panel account-panel">
      <div><h3>Account access</h3><p>{employee.user ? `Linked user account: ${employee.user}` : 'No user account is linked to this employee.'}</p></div>
      <div className="table-actions">
        {!employee.user && canProvision && <button className="link-button" type="button" disabled={busy || !contact.company_email} title={!contact.company_email ? 'Add a company email before provisioning an account' : undefined} onClick={() => runAction(() => provisionEmployeeAccount(id), 'Employee account provisioned.')}><UserPlus size={16}/> Provision account</button>}
        {employee.user && canInvite && <button className="link-button" type="button" disabled={busy} onClick={() => runAction(() => inviteEmployeeAccount(id), 'Account setup invitation sent.')}><Mail size={16}/> Send setup invitation</button>}
      </div>
    </section>
    <div className="detail-grid">
      <InfoCard title="Contact"><Info icon={Mail} label="Company email" value={contact.company_email}/><Info icon={Mail} label="Personal email" value={contact.personal_email}/><Info icon={Phone} label="Phone" value={contact.phone_number}/><Info icon={Phone} label="Other number" value={contact.other_phone_number}/><Info icon={Phone} label="CUG number" value={contact.cug_phone_number}/><Info icon={MapPin} label="Address" value={contact.address}/></InfoCard>
      <InfoCard title="Next of kin">{employee.next_of_kin?.length ? employee.next_of_kin.map(kin => <div key={kin.id}><Info label={kin.is_primary ? 'Primary contact' : 'Full name'} value={kin.full_name}/><Info label="Relationship" value={kin.relationship}/><Info icon={Phone} label="Phone" value={kin.phone_number}/><Info icon={Mail} label="Email" value={kin.email}/><Info icon={MapPin} label="Address" value={kin.address}/></div>) : <p>No next of kin added.</p>}</InfoCard>
      <InfoCard title="Identity"><Info label="Employee number" value={employee.employee_number}/><Info label="Date of birth" value={identity.date_of_birth}/><Info label="Gender" value={identity.gender}/></InfoCard>
      <InfoCard title="Employment"><Info label="Type" value={employment.employment_type}/><Info label="Status" value={employment.employment_status}/><Info label="Resumption date" value={employment.employment_start_date}/><Info label="Probation end" value={employment.probation_end_date}/><Info label="Confirmation date" value={employment.confirmation_date}/><Info label="Confirmation status" value={employment.confirmation_status}/><Info label="Resignation date" value={employment.date_left}/></InfoCard>
      <InfoCard title="Assignment"><Info label="Branch" value={assignment.branch_name}/><Info label="Department" value={assignment.department_name}/><Info label="Unit" value={assignment.team_name}/><Info label="Position" value={assignment.position_name}/><Info label="Job grade" value={assignment.job_grade_name}/><Info label="Manager ID" value={assignment.manager}/></InfoCard>
    </div>
  </div>;
}

function InfoCard({title, children}) {
  return <section className="panel info-card"><h3>{title}</h3>{children}</section>;
}

function Info({icon: Icon, label, value}) {
  return <div className="info"><div>{Icon && <Icon size={16}/>}<small>{label}</small></div><strong>{value || '—'}</strong></div>;
}
