import React, {useEffect, useState} from 'react';
import {Link, useNavigate, useParams} from 'react-router-dom';
import {ArrowLeft, Save} from 'lucide-react';
import {createEmployee, getEmployee, listEmployees, updateEmployee} from '../api/employees';
import {listBranches, listDepartments, listTeams, listJobGrades, listPositions} from '../api/organization';

const blankForm = {
  identity: {first_name: '', middle_name: '', last_name: '', date_of_birth: '', gender: ''},
  contact: {personal_email: '', company_email: '', phone_number: '', other_phone_number: '', cug_phone_number: '', address: ''},
  next_of_kin: [],
  assignment: {branch: '', department: '', team: '', position: '', position_title: '', job_grade: '', manager: ''},
  employment: {employment_type: 'PERMANENT', employment_status: 'PROBATION', employment_start_date: '', probation_end_date: '', confirmation_status: 'PENDING', confirmation_date: '', date_left: ''},
};

const assignmentFields = ['branch', 'department', 'team', 'position', 'position_title', 'job_grade', 'manager'];

function employeePayload(form) {
  const payload = structuredClone(form);
  if (!payload.identity.date_of_birth) payload.identity.date_of_birth = null;
  for (const field of assignmentFields) payload.assignment[field] = payload.assignment[field] || null;
  for (const field of ['employment_start_date', 'probation_end_date', 'confirmation_date', 'date_left']) {
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
  const [employees, setEmployees] = useState([]);
  const [structure, setStructure] = useState({branches: [], departments: [], teams: [], jobGrades: [], positions: []});

  useEffect(() => {
    if (!editing) return;
    getEmployee(id).then(employee => {
      setForm({
        identity: Object.fromEntries(Object.keys(blankForm.identity).map(field => [field, employee.identity?.[field] ?? blankForm.identity[field]])),
        contact: Object.fromEntries(Object.keys(blankForm.contact).map(field => [field, employee.contact?.[field] ?? blankForm.contact[field]])),
        next_of_kin: employee.next_of_kin || [],
        assignment: {
          ...Object.fromEntries(assignmentFields.map(field => [field, employee.assignment?.[field] || ''])),
          position_title: employee.assignment?.position_name || '',
        },
        employment: Object.fromEntries(Object.keys(blankForm.employment).map(field => [field, employee.employment?.[field] ?? blankForm.employment[field]])),
      });
    }).catch(requestError => setError(requestError.message));
  }, [editing, id]);

  useEffect(() => {
    Promise.allSettled([listBranches(), listDepartments(), listTeams(), listJobGrades(), listPositions()])
      .then(results => {
        const values = results.map(result => result.status === 'fulfilled' ? result.value?.results || result.value || [] : []);
        setStructure({ branches: values[0], departments: values[1], teams: values[2], jobGrades: values[3], positions: values[4] });
        const failed = results.find(result => result.status === 'rejected');
        if (failed) setError(failed.reason?.message || 'Some organization options could not be loaded.');
      });
  }, []);

  const updateField = (section, field, value) => {
    setForm(current => ({...current, [section]: {...current[section], [field]: value}}));
  };

  useEffect(() => {
    listEmployees().then(data => setEmployees(Array.isArray(data) ? data : data?.results || []))
      .catch(requestError => setError(requestError.message));
  }, []);

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
        <SelectField label="Gender" value={form.identity.gender} onChange={value => updateField('identity', 'gender', value)} options={[...new Set(['', 'Male', 'Female', 'Other', 'Prefer not to say', form.identity.gender].filter(value => value !== undefined))]}/>
      </FormSection>
      <FormSection title="Contact information">
        <Field label="Company email" type="email" value={form.contact.company_email} onChange={value => updateField('contact', 'company_email', value)}/>
        <Field label="Personal email" type="email" value={form.contact.personal_email} onChange={value => updateField('contact', 'personal_email', value)}/>
        <Field label="Phone number" type="tel" value={form.contact.phone_number} onChange={value => updateField('contact', 'phone_number', value)}/>
        <Field label="Other number" type="tel" value={form.contact.other_phone_number} onChange={value => updateField('contact', 'other_phone_number', value)}/>
        <Field label="CUG number" type="tel" value={form.contact.cug_phone_number} onChange={value => updateField('contact', 'cug_phone_number', value)}/>
        <Field label="Address" value={form.contact.address} onChange={value => updateField('contact', 'address', value)} wide/>
      </FormSection>
      <FormSection title="Next of kin">
        {form.next_of_kin.map((kin, index) => <div className="wide form-grid" key={index}>
          {['full_name', 'relationship', 'phone_number', 'email', 'address'].map(field => <Field key={field} label={{full_name: 'Full name', relationship: 'Relationship', phone_number: 'Phone number', email: 'Email', address: 'Address'}[field]} type={field === 'email' ? 'email' : field === 'phone_number' ? 'tel' : 'text'} value={kin[field]} required={['full_name', 'relationship', 'phone_number'].includes(field)} onChange={value => setForm(current => ({...current, next_of_kin: current.next_of_kin.map((item, i) => i === index ? {...item, [field]: value} : item)}))}/>)}
          <label className="field"><span>Primary contact</span><input type="checkbox" checked={Boolean(kin.is_primary)} onChange={event => { const checked = event.target.checked; setForm(current => ({...current, next_of_kin: current.next_of_kin.map((item, i) => ({...item, is_primary: i === index ? checked : false}))})); }}/></label>
          <button className="link-button" type="button" onClick={() => setForm(current => ({...current, next_of_kin: current.next_of_kin.filter((_, i) => i !== index)}))}>Remove contact</button>
        </div>)}
        <button className="link-button" type="button" onClick={() => setForm(current => ({...current, next_of_kin: [...current.next_of_kin, {full_name: '', relationship: '', phone_number: '', email: '', address: '', is_primary: current.next_of_kin.length === 0}]}))}>Add next of kin</button>
      </FormSection>
      <FormSection title="Assignment">
        <p className="form-hint wide">Select the employee's internal organization assignment.</p>
        <SelectObjectField label="Branch" value={form.assignment.branch} onChange={value => updateField('assignment', 'branch', value)} options={structure.branches} valueKey="id" labelKey="name"/>
        <SelectObjectField label="Department" value={form.assignment.department} onChange={value => updateField('assignment', 'department', value)} options={structure.departments} valueKey="id" labelKey="name"/>
        <SelectObjectField label="Unit" value={form.assignment.team} onChange={value => updateField('assignment', 'team', value)} options={structure.teams} valueKey="id" labelKey="name"/>
        <Field label="Position" value={form.assignment.position_title} onChange={value => updateField('assignment', 'position_title', value)} placeholder="Enter position title"/>
        <SelectObjectField label="Job grade" value={form.assignment.job_grade} onChange={value => updateField('assignment', 'job_grade', value)} options={structure.jobGrades.filter(grade => grade.is_active !== false && grade.name?.toLowerCase() !== 'associate')} valueKey="id" labelKey="name"/>
        <SelectObjectField label="Manager" value={form.assignment.manager} onChange={value => updateField('assignment', 'manager', value)} options={employees.filter(employee => employee.id !== id && (employee.is_active || employee.id === form.assignment.manager)).map(employee => ({id: employee.id, name: `${[employee.identity?.first_name, employee.identity?.last_name].filter(Boolean).join(' ')} (${employee.employee_number})`}))} valueKey="id" labelKey="name"/>
      </FormSection>
      <FormSection title="Employment">
        <SelectField label="Employment type" value={form.employment.employment_type} onChange={value => updateField('employment', 'employment_type', value)} options={['PERMANENT', 'CONTRACT', 'INTERN']}/>
        <SelectField label="Employment status" value={form.employment.employment_status} onChange={value => updateField('employment', 'employment_status', value)} options={['ACTIVE', 'PROBATION', 'RESIGNED', 'RETIRED', 'TERMINATED']}/>
        <Field label="Resumption date" type="date" value={form.employment.employment_start_date} onChange={value => updateField('employment', 'employment_start_date', value)}/>
        <Field label="Probation end" type="date" value={form.employment.probation_end_date} onChange={value => updateField('employment', 'probation_end_date', value)}/>
        <Field label="Confirmation date" type="date" value={form.employment.confirmation_date} onChange={value => updateField('employment', 'confirmation_date', value)}/>
        <SelectField label="Confirmation status" value={form.employment.confirmation_status} onChange={value => updateField('employment', 'confirmation_status', value)} options={['NOT_APPLICABLE', 'PENDING', 'CONFIRMED', 'EXTENDED']}/>
        <Field label="Resignation / retirement / termination date" type="date" value={form.employment.date_left} onChange={value => updateField('employment', 'date_left', value)}/>
      </FormSection>
      <div className="form-actions"><Link className="link-button" to={editing ? `/employees/${id}` : '/employees'}>Cancel</Link><button className="primary" type="submit" disabled={busy}><Save size={17}/>{busy ? 'Saving…' : editing ? 'Save changes' : 'Create employee'}</button></div>
    </form>
  </div>;
}

function FormSection({title, children}) {
  return <section className="panel form-section"><h3>{toTitleCase(title)}</h3><div className="form-grid">{children}</div></section>;
}

function Field({label, type = 'text', value, onChange, required, wide, placeholder}) {
  return <label className={`field${wide ? ' wide' : ''}`}>{toTitleCase(label)}<input type={type} value={value || ''} onChange={event => onChange(event.target.value)} required={required} placeholder={placeholder}/></label>;
}

function SelectField({label, value, onChange, options}) {
  return <label className="field">{toTitleCase(label)}<select value={value || ''} onChange={event => onChange(event.target.value)}>{options.map(option => <option key={option} value={option}>{option ? toTitleCase(option.replaceAll('_', ' ')) : 'Not Specified'}</option>)}</select></label>;
}

function SelectObjectField({label, value, onChange, options, valueKey, labelKey}) {
  return <label className="field">{toTitleCase(label)}<select value={value || ''} onChange={event => onChange(event.target.value)}><option value="">Not Assigned</option>{options.map(option => <option key={option[valueKey]} value={option[valueKey]}>{option[labelKey]}</option>)}</select></label>;
}

function toTitleCase(value) {
  return String(value).replace(/\b\w/g, character => character.toUpperCase());
}
