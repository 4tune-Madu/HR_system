import React, { useEffect, useState } from 'react';
import { BriefcaseBusiness, Building2, Mail, MapPin, Phone, ShieldCheck, UserRound } from 'lucide-react';
import { getEmployee } from '../api/employees';
import { useAuth } from '../context/AuthContext';

const display = (value) => value || 'Not provided';
const fullName = (employee, user) => [employee?.identity?.first_name || user?.first_name, employee?.identity?.middle_name, employee?.identity?.last_name || user?.last_name].filter(Boolean).join(' ') || 'Employee';

export default function MyProfile() {
  const { user } = useAuth();
  const [employee, setEmployee] = useState(null);
  const [error, setError] = useState('');
  const membership = user?.memberships?.find((item) => item.organization_id === import.meta.env.VITE_ORGANIZATION_ID);

  useEffect(() => {
    if (!user?.employee_id) return;
    getEmployee(user.employee_id).then(setEmployee).catch((requestError) => setError(requestError.message));
  }, [user?.employee_id]);

  const identity = employee?.identity || {};
  const contact = employee?.contact || {};
  const assignment = employee?.assignment || {};
  const employment = employee?.employment || {};
  const employeeName = fullName(employee, user);

  return <div className="profile-page">
    <div className="page-heading profile-heading"><div><span className="eyebrow">Employee self-service</span><h2>My Profile</h2><p>Review all personal, contact, employment, and organizational details held for your employee record.</p></div><div className="profile-avatar"><UserRound size={28} /></div></div>
    {error && <div className="error banner">{error}</div>}

    <section className="panel profile-card profile-summary"><div className="profile-card-heading"><span className="profile-card-icon"><UserRound size={19} /></span><div><h3>{employeeName}</h3><p>{display(employee?.employee_number)} · {membership?.organization_name || 'Organization'}</p></div><span className="status active">{user?.is_active ? 'Active' : 'Inactive'}</span></div></section>

    <div className="profile-grid">
      <ProfileSection title="Personal information" icon={UserRound} items={[["First name", identity.first_name], ["Middle name", identity.middle_name], ["Last name", identity.last_name], ["Date of birth", identity.date_of_birth], ["Gender", identity.gender]]} />
      <ProfileSection title="Contact information" icon={Mail} items={[["Company email", contact.company_email || user?.email], ["Personal email", contact.personal_email], ["Phone number", contact.phone_number], ["Other number", contact.other_phone_number], ["CUG number", contact.cug_phone_number], ["Address", contact.address]]} />
      <ProfileSection title="Employment" icon={BriefcaseBusiness} items={[["Employment type", employment.employment_type], ["Employment status", employment.employment_status], ["Resumption date", employment.employment_start_date], ["Probation end", employment.probation_end_date], ["Confirmation date", employment.confirmation_date], ["Confirmation status", employment.confirmation_status], ["Date left", employment.date_left]]} />
      <ProfileSection title="Organization assignment" icon={Building2} items={[["Branch", assignment.branch_name], ["Department", assignment.department_name], ["Unit", assignment.team_name], ["Position", assignment.position_name], ["Job grade", assignment.job_grade_name], ["Manager", assignment.manager_name]]} />
    </div>

    <section className="panel profile-card"><div className="profile-card-heading"><span className="profile-card-icon"><MapPin size={19} /></span><div><h3>Next of kin</h3><p>Emergency contact details held on your employee record.</p></div></div>{employee?.next_of_kin?.length ? <div className="profile-grid profile-next-of-kin">{employee.next_of_kin.map((kin) => <div className="profile-details" key={kin.id}><ProfileDetail icon={UserRound} label="Full name" value={kin.full_name} /><ProfileDetail icon={Phone} label="Phone" value={kin.phone_number} /><ProfileDetail icon={Mail} label="Email" value={kin.email} /><ProfileDetail icon={MapPin} label="Relationship" value={kin.relationship} /></div>)}</div> : <p className="empty">No next-of-kin information has been added.</p>}</section>
    <section className="panel profile-help"><ShieldCheck size={23} /><div><h3>Need to update your details?</h3><p>Contact HR to update employment, contact, or organizational information. Changes remain subject to company approval.</p></div></section>
  </div>;
}

function ProfileSection({ title, icon: Icon, items }) {
  return <section className="panel profile-card"><div className="profile-card-heading"><span className="profile-card-icon"><Icon size={19} /></span><div><h3>{title}</h3><p>Information from your employee record.</p></div></div><div className="profile-details profile-detail-grid">{items.map(([label, value]) => <ProfileDetail key={label} icon={Icon} label={label} value={display(value)} />)}</div></section>;
}

function ProfileDetail({ icon: Icon, label, value }) { return <div className="profile-detail"><Icon size={16} /><div><small>{label}</small><strong>{value}</strong></div></div>; }
