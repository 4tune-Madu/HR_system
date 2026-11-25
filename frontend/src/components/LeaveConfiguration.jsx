import React, {useEffect, useState} from 'react';
import {saveLeavePolicy, createPublicHoliday, initializeLeaveBalances, listWorkSchedules, saveWorkSchedule} from '../api/leave';

export default function LeaveConfiguration({types, policies, canManage, onSaved, isEmployee = false}) {
  const [selected, setSelected] = useState('');
  const [form, setForm] = useState({days_per_year: '', minimum_days_per_request: '1', maximum_days_per_request: '', allow_carry_forward: false, maximum_carry_forward_days: ''});
  const [holiday, setHoliday] = useState({name: '', date: '', description: ''});
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [year, setYear] = useState(new Date().getFullYear());
  const [schedule, setSchedule] = useState({code: 'STANDARD', name: 'Standard working week', monday: true, tuesday: true, wednesday: true, thursday: true, friday: true, saturday: false, sunday: false, is_default: true});
  useEffect(() => {
    listWorkSchedules().then(data => {
      const existing = (data.results || data).find(item => item.is_default && item.is_active);
      if (existing) setSchedule(existing);
    }).catch(error => setMessage(error.message));
  }, []);
  const saveSchedule = async event => {
    event.preventDefault(); setBusy(true); setMessage('');
    try {
      setSchedule(await saveWorkSchedule(schedule, schedule.id));
      setMessage('Default working week saved. Employee-specific schedules still take priority.');
    } catch (error) {setMessage(error.message);} finally {setBusy(false);}
  };
  const initialize = async event => {
    event.preventDefault(); setBusy(true); setMessage('');
    try {
      const result = await initializeLeaveBalances(Number(year));
      await onSaved();
      setMessage(`${result.created} employee leave balances created for ${result.year}. Existing balances were preserved.`);
    } catch (error) {setMessage(error.message);} finally {setBusy(false);}
  };
  const policy = policies.find(item => item.leave_type === selected);
  const choose = id => {
    setSelected(id);
    const existing = policies.find(item => item.leave_type === id);
    setForm({days_per_year: existing?.days_per_year ?? '', minimum_days_per_request: existing?.minimum_days_per_request ?? '1', maximum_days_per_request: existing?.maximum_days_per_request ?? '', allow_carry_forward: existing?.allow_carry_forward ?? false, maximum_carry_forward_days: existing?.maximum_carry_forward_days ?? ''});
  };
  const save = async (event, isHoliday) => {
    event.preventDefault(); setBusy(true); setMessage('');
    try {
      if (isHoliday) {
        await createPublicHoliday(holiday);
        setHoliday({name: '', date: '', description: ''});
      } else {
        await saveLeavePolicy({...form, leave_type: selected, maximum_days_per_request: form.maximum_days_per_request || null, maximum_carry_forward_days: form.allow_carry_forward ? form.maximum_carry_forward_days || null : null}, policy?.id);
      }
      await onSaved();
      setMessage(isHoliday ? 'Public holiday added. This date is excluded from new leave calculations.' : 'Leave policy saved.');
    } catch (error) { setMessage(error.message); } finally { setBusy(false); }
  };
  return <section className="panel">
    <h3>{isEmployee ? 'My leave entitlements' : 'Leave entitlements and rules'}</h3>
    <p>{isEmployee ? 'Review the leave types and allowances available to you. Only working days count; public holidays and scheduled days off are excluded.' : 'Leave can be taken in separate requests up to the available balance. Only working days count; active public holidays and scheduled days off are excluded.'}</p>
    <div className="table-wrap"><table><thead><tr><th>Leave type</th><th>Days per year</th><th>Days per request</th><th>Policy</th></tr></thead><tbody>{types.map(type => {
      const item = policies.find(p => p.leave_type === type.id);
      return <tr key={type.id}><td>{type.name}</td><td>{item ? item.days_per_year : 'Not configured'}</td><td>{item ? `${item.minimum_days_per_request} minimum · ${item.maximum_days_per_request ?? 'Available balance'} maximum` : 'Not configured'}</td><td>{type.description || (type.is_paid ? 'Paid leave' : 'Unpaid leave')}{item && ` · ${item.is_active ? 'Active' : 'Inactive'} · Carry forward ${item.allow_carry_forward ? `up to ${item.maximum_carry_forward_days ?? 'policy limit'} days` : 'disabled'}`}</td></tr>;
    })}</tbody></table></div>
    {message && <p role="status">{message}</p>}
    {canManage ? <div className="attendance-layout">
      <form className="device-action" onSubmit={event => save(event, false)}>
        <h3>Configure policy</h3>
        <label className="field">Leave type<select required value={selected} onChange={event => choose(event.target.value)}><option value="">Select leave type</option>{types.map(type => <option key={type.id} value={type.id}>{type.name}</option>)}</select></label>
        {[['days_per_year', 'Days per year'], ['minimum_days_per_request', 'Minimum days per request'], ['maximum_days_per_request', 'Maximum days per request (optional)']].map(([key, label]) => <label className="field" key={key}>{label}<input type="number" min="0" step="1" required={key !== 'maximum_days_per_request'} value={form[key]} onChange={event => setForm({...form, [key]: event.target.value})}/></label>)}
        <label><input type="checkbox" checked={form.allow_carry_forward} onChange={event => setForm({...form, allow_carry_forward: event.target.checked})}/> Allow carry forward</label>
        {form.allow_carry_forward && <label className="field">Maximum carry-forward days<input type="number" min="0" step="1" required value={form.maximum_carry_forward_days} onChange={event => setForm({...form, maximum_carry_forward_days: event.target.value})}/></label>}
        <button className="primary" disabled={busy || !selected}>Save policy</button>
      </form>
      <form className="device-action" onSubmit={event => save(event, true)}>
        <h3>Add public holiday</h3><p>Enter each officially observed date, including any substitute holiday.</p>
        <label className="field">Holiday name<input required value={holiday.name} onChange={event => setHoliday({...holiday, name: event.target.value})}/></label>
        <label className="field">Observed date<input type="date" required value={holiday.date} onChange={event => setHoliday({...holiday, date: event.target.value})}/></label>
        <label className="field">Notes<input value={holiday.description} onChange={event => setHoliday({...holiday, description: event.target.value})}/></label>
        <button className="primary" disabled={busy}>Add holiday</button>
      </form>
      <form className="device-action" onSubmit={initialize}>
        <h3>Initialize annual balances</h3><p>After saving policies, create missing balances for active employees. Existing entitlements and days already used are preserved.</p>
        <label className="field">Year<input required type="number" min="1900" max="9999" value={year} onChange={event => setYear(event.target.value)}/></label>
        <button className="primary" disabled={busy}>Initialize balances</button>
      </form>
      <form className="device-action" onSubmit={saveSchedule}>
        <h3>Default working week</h3><p>{schedule.id ? 'Saved working days' : 'Choose and save the company working days before requesting leave.'}</p>
        {['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].map(day => <label key={day}><input type="checkbox" checked={schedule[day]} onChange={event => setSchedule({...schedule, [day]: event.target.checked})}/> {day[0].toUpperCase() + day.slice(1)}</label>)}
        <button className="primary" disabled={busy}>Save working week</button>
      </form>
    </div> : !isEmployee && <p>A user with leave management permission can configure annual allowances and public holidays.</p>}
  </section>;
}
