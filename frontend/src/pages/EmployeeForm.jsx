import React, {useEffect, useState} from 'react';
import {Link, useNavigate, useParams} from 'react-router-dom';
import {ArrowLeft, Save} from 'lucide-react';
import {createEmployee, getEmployee, updateEmployee} from '../api/employees';

const blankForm = {
  identity: {first_name: '', middle_name: '', last_name: '', date_of_birth: '', gender: ''},
  contact: {personal_email: '', company_email: '', phone_number: '', address: ''},
  assignment: {branch: '', department: '', team: '', position: '', job_grade: '', manager: ''},
  employment: {employment_type: 'PERMANENT', employment_status: 'PROBATION', offer_date: '', employment_start_date: '', probation_end_date: '', confirmation_status: 'PENDING', confirmation_date: '', date_left: ''},
};

const assignmentFields = ['branch', 'department', 'team', 'position', 'job_grade', 'manager'];

function employeePayload(form) {
  const payload = structuredClone(form);
  if (!payload.identity.date_of_birth) payload.identity.date_of_birth = null;
  for (const field of assignmentFields) payload.assignment[field] = payload.assignment[field] || null;
  for (const field of ['offer_date', 'employment_start_date', 'probation_end_date', 'confirmation_date', 'date_left']) {
    if (!payload.employment[field]) payload.employment[field] = null;
  }
  return payload;
}

export default function EmployeeForm() {
  const {id} = useParams();
  const editing = Boolean(id);
  const navigate = useNavigate();
  const [form, setForm] = useState(() => structuredClone(blankForm));
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!editing) return;
    getEmployee(id).then(employee => {
      setForm({
        identity: Object.fromEntries(Object.keys(blankForm.identity).map(field => [field, employee.identity?.[field] ?? blankForm.identity[field]])),
        contact: Object.fromEntries(Object.keys(blankForm.contact).map(field => [field, employee.contact?.[field] ?? blankForm.contact[field]])),
        assignment: Object.fromEntries(assignmentFields.map(field => [field, employee.assignment?.[field] || ''])),
        employment: Object.fromEntries(Object.keys(blankForm.employment).map(field => [field, employee.employment?.[field] ?? blankForm.employment[field]])),
      });
    }).catch(requestError => setError(requestError.message));
  }, [editing, id]);

  const updateField = (section, field, value) => {
    setForm(current => ({...current, [section]: {...current[section], [field]: value}}));
  };

  const submit = async event => {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const payload = employeePayload(form);
      const saved = editing ? await updateEmployee(id, payload) : await createEmployee(payload);
      navigate(`/employees/${saved.id}`);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  return <div>
    <Link className="back" to={editing ? `/employees/${id}` : '/employees'}><ArrowLeft size={17}/> Back to employees</Link>
    <div className="page-heading"><div><span className="eyebrow">Employees</span><h2>{editing ? 'Edit employee' : 'Add employee'}</h2><p>{editing ? 'Update this employee record.' : 'Create an employee record.'}</p></div></div>
    {error && <div className="error banner" role="alert">{error}</div>}
    <form className="employee-form" onSubmit={submit}>
      <FormSection title="Personal information">
        <Field label="First name" value={form.identity.first_name} onChange={value => updateField('identity', 'first_name', value)} required/>
        <Field label="Middle name" value={form.identity.middle_name} onChange={value => updateField('identity', 'middle_name', value)}/>
        <Field label="Last name" value={form.identity.last_name} onChange={value => updateField('identity', 'last_name', value)} required/>
        <Field label="Date of birth" type="date" value={form.identity.date_of_birth} onChange={value => updateField('identity', 'date_of_birth', value)}/>
        <Field label="Gender" value={form.identity.gender} onChange={value => updateField('identity', 'gender', value)}/>
      </FormSection>
      <FormSection title="Contact information">
        <Field label="Company email" type="email" value={form.contact.company_email} onChange={value => updateField('contact', 'company_email', value)}/>
        <Field label="Personal email" type="email" value={form.contact.personal_email} onChange={value => updateField('contact', 'personal_email', value)}/>
        <Field label="Phone number" type="tel" value={form.contact.phone_number} onChange={value => updateField('contact', 'phone_number', value)}/>
        <Field label="Address" value={form.contact.address} onChange={value => updateField('contact', 'address', value)} wide/>
      </FormSection>
      <FormSection title="Assignment">
        <p className="form-hint wide">Use organization record UUIDs. Leave a field blank if it does not apply.</p>
        {assignmentFields.map(field => <Field key={field} label={`${field.replace('_', ' ')} UUID`} value={form.assignment[field]} onChange={value => updateField('assignment', field, value)} placeholder="Optional UUID"/>)}
      </FormSection>
      <FormSection title="Employment">
        <SelectField label="Employment type" value={form.employment.employment_type} onChange={value => updateField('employment', 'employment_type', value)} options={['PERMANENT', 'CONTRACT', 'TEMPORARY', 'INTERN', 'PART_TIME']}/>
        <SelectField label="Employment status" value={form.employment.employment_status} onChange={value => updateField('employment', 'employment_status', value)} options={['ACTIVE', 'PROBATION', 'SUSPENDED', 'RESIGNED', 'TERMINATED', 'RETIRED']}/>
        <Field label="Offer date" type="date" value={form.employment.offer_date} onChange={value => updateField('employment', 'offer_date', value)}/>
        <Field label="Start date" type="date" value={form.employment.employment_start_date} onChange={value => updateField('employment', 'employment_start_date', value)}/>
        <Field label="Probation end" type="date" value={form.employment.probation_end_date} onChange={value => updateField('employment', 'probation_end_date', value)}/>
        <SelectField label="Confirmation status" value={form.employment.confirmation_status} onChange={value => updateField('employment', 'confirmation_status', value)} options={['NOT_APPLICABLE', 'PENDING', 'CONFIRMED', 'EXTENDED', 'FAILED']}/>
        <Field label="Confirmation date" type="date" value={form.employment.confirmation_date} onChange={value => updateField('employment', 'confirmation_date', value)}/>
        <Field label="Date left" type="date" value={form.employment.date_left} onChange={value => updateField('employment', 'date_left', value)}/>
      </FormSection>
      <div className="form-actions"><Link className="link-button" to={editing ? `/employees/${id}` : '/employees'}>Cancel</Link><button className="primary" type="submit" disabled={busy}><Save size={17}/>{busy ? 'Saving…' : editing ? 'Save changes' : 'Create employee'}</button></div>
    </form>
  </div>;
}

function FormSection({title, children}) {
  return <section className="panel form-section"><h3>{title}</h3><div className="form-grid">{children}</div></section>;
}

function Field({label, type = 'text', value, onChange, required, wide, placeholder}) {
  return <label className={`field${wide ? ' wide' : ''}`}>{label}<input type={type} value={value || ''} onChange={event => onChange(event.target.value)} required={required} placeholder={placeholder}/></label>;
}

function SelectField({label, value, onChange, options}) {
  return <label className="field">{label}<select value={value || ''} onChange={event => onChange(event.target.value)}>{options.map(option => <option key={option} value={option}>{option.replaceAll('_', ' ')}</option>)}</select></label>;
}
