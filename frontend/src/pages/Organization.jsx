import React, { useEffect, useMemo, useState } from 'react';
import { Building2, Check, Pencil, Plus, Trash2 } from 'lucide-react';
import {
  createStructureItem,
  deleteStructureItem,
  getAttendanceSettings,
  listBranches,
  listDepartments,
  listJobGrades,
  listPositions,
  listTeams,
  updateAttendanceSettings,
  updateStructureItem,
} from '../api/organization';
import { useAuth } from '../context/AuthContext';

const resources = [
  { key: 'branches', label: 'Branches', endpoint: 'branches', fields: ['name', 'code', 'address'] },
  { key: 'departments', label: 'Departments', endpoint: 'departments', fields: ['name', 'code', 'description'] },
  { key: 'teams', label: 'Units', endpoint: 'teams', fields: ['name', 'code', 'department', 'description'] },
  { key: 'jobGrades', label: 'Job grades', endpoint: 'job-grades', fields: ['name', 'code', 'description'] },
  { key: 'positions', label: 'Positions', endpoint: 'positions', fields: ['title', 'code', 'department', 'job_grade', 'description'] },
];

const emptyForm = { name: '', title: '', code: '', address: '', description: '', level: '', department: '', job_grade: '' };
const generateJobGradeCode = value => value.trim().toUpperCase().replace(/[^A-Z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 30);

export default function Organization() {
  const { user } = useAuth();
  const membership = user?.memberships?.find((item) => item.organization_id === import.meta.env.VITE_ORGANIZATION_ID);
  const canManageAttendance = user?.is_system_admin || membership?.permissions?.includes('attendance.settings.manage');
  const [data, setData] = useState({ branches: [], departments: [], teams: [], jobGrades: [], positions: [] });
  const [settings, setSettings] = useState({ automatic_attendance_checkout_enabled: true });
  const [activeResource, setActiveResource] = useState('branches');
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [branches, departments, teams, jobGrades, positions, attendanceSettings] = await Promise.all([
        listBranches(), listDepartments(), listTeams(), listJobGrades(), listPositions(), canManageAttendance ? getAttendanceSettings() : Promise.resolve(null),
      ]);
      const values = [branches, departments, teams, jobGrades, positions].map(value => value?.results || value || []);
      setData({ branches: values[0], departments: values[1], teams: values[2], jobGrades: values[3], positions: values[4] });
      if (attendanceSettings) setSettings(attendanceSettings);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [canManageAttendance]);

  const resource = useMemo(() => resources.find(item => item.key === activeResource), [activeResource]);
  const items = data[activeResource] || [];

  const updateForm = (field, value) => setForm(current => ({
    ...current,
    [field]: value,
    ...(activeResource === 'jobGrades' && field === 'name' && !editing ? { code: generateJobGradeCode(value) } : {}),
  }));

  const startEdit = item => {
    setEditing(item.id);
    setForm({ ...emptyForm, ...item, level: item.level ?? '', department: item.department ?? '', job_grade: item.job_grade ?? '' });
    setSuccess('');
  };

  const cancelEdit = () => { setEditing(null); setForm(emptyForm); };

  const save = async event => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    const payload = Object.fromEntries(resource.fields.map(field => [field, form[field] || (field === 'level' ? null : '')]));
    if (resource.key === 'jobGrades') payload.code = generateJobGradeCode(form.name);
    try {
      if (editing) await updateStructureItem(resource.endpoint, editing, payload);
      else await createStructureItem(resource.endpoint, payload);
      cancelEdit();
      await load();
      setSuccess(`${resource.label.slice(0, -1)} ${editing ? 'updated' : 'created'} successfully.`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const remove = async item => {
    if (!window.confirm(`Delete ${item.name || item.title}?`)) return;
    setError('');
    try {
      await deleteStructureItem(resource.endpoint, item.id);
      await load();
      setSuccess(`${resource.label.slice(0, -1)} deleted.`);
    } catch (err) {
      setError(err.message);
    }
  };

  const saveAttendanceSetting = async event => {
    const value = event.target.checked;
    try {
      const updated = await updateAttendanceSettings({ automatic_attendance_checkout_enabled: value });
      setSettings(updated || { automatic_attendance_checkout_enabled: value });
      setSuccess('Attendance setting updated successfully.');
    } catch (err) {
      setError(err.message);
    }
  };

  return <div>
    <div className="page-heading">
      <div><span className="eyebrow">Internal administration</span><h2>Organization structure</h2><p>Manage the internal workforce structure used by employee records.</p></div>
    </div>
    {error && <div className="error banner">{error}</div>}
    {success && <div className="success banner">{success}</div>}

    <div className="panel">
      <div className="panel-head"><div><h3><Building2 size={18} /> Workforce structure</h3><p>Create and maintain internal organization records.</p></div></div>
      <div className="table-actions" style={{ flexWrap: 'wrap', gap: '8px', marginBottom: '18px' }}>
        {resources.map(item => <button key={item.key} type="button" className={activeResource === item.key ? 'primary' : 'link-button'} onClick={() => { setActiveResource(item.key); cancelEdit(); }}>{item.label} ({data[item.key].length})</button>)}
      </div>
      <form onSubmit={save} className="form-grid" style={{ marginBottom: '22px' }}>
        {resource.fields.map(field => {
          if (field === 'department' || field === 'job_grade') {
            const options = field === 'department' ? data.departments : data.jobGrades;
            return <label className="field" key={field}>{field === 'department' ? 'Department' : 'Job grade'}<select value={form[field]} onChange={event => updateForm(field, event.target.value)}><option value="">Not assigned</option>{options.map(option => <option key={option.id} value={option.id}>{option.name}</option>)}</select></label>;
          }
          return <label className="field" key={field}>{field.replace('_', ' ')}<input type={field === 'level' ? 'number' : 'text'} value={form[field]} onChange={event => updateForm(field, event.target.value)} readOnly={resource.key === 'jobGrades' && field === 'code'} placeholder={resource.key === 'jobGrades' && field === 'code' ? 'Generated from name' : undefined} required={['name', 'title', 'code'].includes(field)} /></label>;
        })}
        <div className="form-actions wide"><button className="primary" type="submit" disabled={saving}><Plus size={16} />{editing ? 'Save changes' : 'Add record'}</button>{editing && <button className="link-button" type="button" onClick={cancelEdit}>Cancel</button>}</div>
      </form>
      {loading ? <p>Loading organization structure…</p> : <div className="table-wrap"><table><thead><tr><th>Name</th><th>Code</th><th>Status</th><th /></tr></thead><tbody>{items.length ? items.map(item => <tr key={item.id}><td><strong>{item.name || item.title}</strong></td><td>{item.code || '—'}</td><td>{item.is_active ? 'Active' : 'Inactive'}</td><td><button className="link-button" type="button" onClick={() => startEdit(item)}><Pencil size={14} /> Edit</button><button className="link-button" type="button" onClick={() => remove(item)}><Trash2 size={14} /> Delete</button></td></tr>) : <tr><td colSpan="4" className="empty">No {resource.label.toLowerCase()} configured.</td></tr>}</tbody></table></div>}
    </div>

    {canManageAttendance && <div className="panel">
      <h3>Attendance settings</h3>
      <label className="toggle-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', padding: '12px 0' }}><div><strong>Automatic attendance checkout</strong><div style={{ color: '#6b7280', marginTop: '4px' }}>Close open attendance records when the configured workday ends.</div></div><input type="checkbox" checked={Boolean(settings.automatic_attendance_checkout_enabled)} onChange={saveAttendanceSetting} /></label>
    </div>}
  </div>;
}
