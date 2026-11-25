import React, { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, ClipboardList } from 'lucide-react';
import { listEmployees } from '../api/employees';
import { createOnboardingTask, listOnboardingTasks, updateOnboardingTask } from '../api/onboarding';
import { useAuth } from '../context/AuthContext';

const statusLabel = (value) => (value || '').replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());

export default function Onboarding() {
  const { user } = useAuth();
  const membership = user?.memberships?.find((item) => item.organization_id === import.meta.env.VITE_ORGANIZATION_ID);
  const canManage = user?.is_system_admin || membership?.permissions?.includes('employee.update');
  const [tasks, setTasks] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({ employee: '', title: '', due_date: '', notes: '' });

  const refresh = () => Promise.all([listOnboardingTasks(), listEmployees()])
    .then(([taskData, employeeData]) => {
      setTasks(Array.isArray(taskData) ? taskData : taskData?.results || []);
      setEmployees(Array.isArray(employeeData) ? employeeData : employeeData?.results || []);
    })
    .catch((error) => setNotice(error.message));

  useEffect(() => { refresh(); }, []);

  const counts = useMemo(() => ({
    total: tasks.length,
    completed: tasks.filter((task) => task.status === 'COMPLETED').length,
    open: tasks.filter((task) => task.status !== 'COMPLETED').length,
  }), [tasks]);

  const createTask = async (event) => {
    event.preventDefault();
    try {
      await createOnboardingTask({ ...form, due_date: form.due_date || null });
      setForm({ employee: '', title: '', due_date: '', notes: '' });
      setNotice('Onboarding task created.');
      refresh();
    } catch (error) { setNotice(error.message); }
  };

  const updateStatus = async (task, status) => {
    try {
      const saved = await updateOnboardingTask(task.id, { status });
      setTasks((current) => current.map((item) => item.id === saved.id ? saved : item));
    } catch (error) { setNotice(error.message); }
  };

  return <div className="attendance-shell">
    <div className="page-heading attendance-header"><div><span className="eyebrow">Internal people operations</span><h2>Onboarding</h2><p>Track internal onboarding tasks for active employees.</p></div><div className="today-pill"><ClipboardList size={18} /> Checklist</div></div>
    {notice && <div className="info banner">{notice}</div>}
    <div className="stats attendance-stats"><Stat label="Tasks" value={counts.total} /><Stat label="Open" value={counts.open} /><Stat label="Completed" value={counts.completed} /></div>
    <div className="attendance-layout">
      {canManage && <form className="panel device-action" onSubmit={createTask}><h3>Add onboarding task</h3><select required value={form.employee} onChange={(event) => setForm({ ...form, employee: event.target.value })}><option value="">Select employee</option>{employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.employee_number} — {employee.identity?.first_name || ''} {employee.identity?.last_name || ''}</option>)}</select><input required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="Task title" /><input type="date" value={form.due_date} onChange={(event) => setForm({ ...form, due_date: event.target.value })} /><textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} placeholder="Notes (optional)" /><button className="primary" type="submit">Add task</button></form>}
      <div className="panel"><h3>Onboarding progress</h3><p>{counts.completed} of {counts.total} tasks completed.</p><div className="bar-track"><span className="bar-fill present" style={{ width: `${counts.total ? (counts.completed / counts.total) * 100 : 0}%` }} /></div></div>
    </div>
    <div className="panel table-panel"><div className="toolbar"><div><h3>Employee onboarding tasks</h3><p>Update task status as internal steps are completed.</p></div></div><div className="table-wrap"><table><thead><tr><th>Employee</th><th>Task</th><th>Due</th><th>Status</th><th>Action</th></tr></thead><tbody>{tasks.length ? tasks.map((task) => <tr key={task.id}><td>{task.employee_number} — {task.employee_name}</td><td><strong>{task.title}</strong>{task.notes && <small>{task.notes}</small>}</td><td>{task.due_date || '—'}</td><td>{statusLabel(task.status)}</td><td>{canManage && (task.status !== 'COMPLETED' ? <button className="primary" type="button" onClick={() => updateStatus(task, 'COMPLETED')}><CheckCircle2 size={15} /> Complete</button> : <button type="button" onClick={() => updateStatus(task, 'TODO')}>Reopen</button>)}</td></tr>) : <tr><td colSpan="5" className="empty">No onboarding tasks created.</td></tr>}</tbody></table></div></div>
  </div>;
}

function Stat({ label, value }) { return <div className="stat attendance-stat"><div><small>{label}</small><strong>{value}</strong></div></div>; }
