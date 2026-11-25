import React, {useEffect, useState} from 'react';
import {listJobGrades, listPositions} from '../api/organization';
import {listSalaryStructures, saveSalaryStructure} from '../api/payroll';

const blank = {job_grade: '', position: '', monthly_base: '', effective_from: '', is_active: true, components: []};
export default function SalaryStructures() {
  const [grades, setGrades] = useState([]);
  const [positions, setPositions] = useState([]);
  const [structures, setStructures] = useState([]);
  const [form, setForm] = useState(blank);
  const [scope, setScope] = useState('job_grade');
  const [editing, setEditing] = useState(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    Promise.all([listJobGrades(), listPositions(), listSalaryStructures()]).then(([g, p, s]) => {
      setGrades(g.results || g); setPositions(p.results || p); setStructures(s.results || s);
    }).catch(error => setMessage(error.message));
  }, []);
  const reset = () => {setForm({...blank, components: []}); setEditing(null);};
  const save = async event => {
    event.preventDefault(); setBusy(true); setMessage('');
    try {
      await saveSalaryStructure({...form, job_grade: scope === 'job_grade' ? form.job_grade : null, position: scope === 'position' ? form.position : null}, editing);
      setStructures(await listSalaryStructures()); reset(); setMessage('Salary structure saved. It applies to newly processed payroll periods.');
    } catch (error) { setMessage(error.message); } finally {setBusy(false);}
  };
  const edit = item => {setEditing(item.id); setScope(item.position ? 'position' : 'job_grade'); setForm({job_grade: item.job_grade || '', position: item.position || '', monthly_base: item.monthly_base, effective_from: item.effective_from, is_active: item.is_active, components: item.components});};
  const changeComponent = (index, key, value) => setForm(current => ({...current, components: current.components.map((item, i) => i === index ? {...item, [key]: value} : item)}));
  return <section className="panel">
    <h3>Pay by job grade or position</h3>
    <p>The latest effective position structure takes priority over the grade structure. An employee-specific compensation record overrides both; employee allowances and deductions are added separately. Amounts are fixed monthly amounts.</p>
    {message && <p role="status">{message}</p>}
    <form className="form-grid" onSubmit={save}>
      <label className="field">Pay basis<select value={scope} onChange={event => setScope(event.target.value)}><option value="job_grade">Job grade</option><option value="position">Position</option></select></label>
      <label className="field">{scope === 'job_grade' ? 'Job grade' : 'Position'}<select required value={form[scope]} onChange={event => setForm({...form, [scope]: event.target.value})}><option value="">Select {scope === 'job_grade' ? 'grade' : 'position'}</option>{(scope === 'job_grade' ? grades : positions).map(item => <option key={item.id} value={item.id}>{item.name || item.title}</option>)}</select></label>
      <label className="field">Monthly base pay<input required type="number" min="0" step="0.01" value={form.monthly_base} onChange={event => setForm({...form, monthly_base: event.target.value})}/></label>
      <label className="field">Effective from<input required type="date" value={form.effective_from} onChange={event => setForm({...form, effective_from: event.target.value})}/></label>
      <label><input type="checkbox" checked={form.is_active} onChange={event => setForm({...form, is_active: event.target.checked})}/> Active</label>
      <div className="wide"><h4>Structure allowances and deductions</h4>{form.components.map((component, index) => <div className="form-grid" key={index}>
        <label className="field">Name<input required maxLength="120" value={component.name} onChange={event => changeComponent(index, 'name', event.target.value)}/></label>
        <label className="field">Type<select value={component.kind} onChange={event => changeComponent(index, 'kind', event.target.value)}><option value="EARNING">Allowance</option><option value="DEDUCTION">Deduction</option></select></label>
        <label className="field">Monthly amount<input required type="number" min="0" step="0.01" value={component.amount} onChange={event => changeComponent(index, 'amount', event.target.value)}/></label>
        <button className="link-button" type="button" onClick={() => setForm({...form, components: form.components.filter((_, i) => i !== index)})}>Remove component</button>
      </div>)}<button className="link-button" type="button" onClick={() => setForm({...form, components: [...form.components, {name: '', kind: 'EARNING', amount: ''}]})}>Add allowance or deduction</button></div>
      <div className="form-actions wide"><button className="primary" disabled={busy}>{editing ? 'Update structure' : 'Save structure'}</button>{editing && <button type="button" onClick={reset}>Cancel edit</button>}</div>
    </form>
    <div className="table-wrap"><table><thead><tr><th>Grade / position</th><th>Monthly base</th><th>Allowances / deductions</th><th>Effective from</th><th>Status</th><th>Action</th></tr></thead><tbody>{structures.map(item => <tr key={item.id}><td>{item.position_name || item.job_grade_name}</td><td>{item.monthly_base}</td><td>{item.components.map((component, index) => <div key={index}>{component.name}: {component.kind === 'DEDUCTION' ? '−' : '+'}{component.amount}</div>)}</td><td>{item.effective_from}</td><td>{item.is_active ? 'Active' : 'Inactive'}</td><td><button type="button" onClick={() => edit(item)}>Edit</button></td></tr>)}{!structures.length && <tr><td colSpan="6">No salary structures configured.</td></tr>}</tbody></table></div>
  </section>;
}
