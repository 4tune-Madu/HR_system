import React, { useEffect, useMemo, useState } from 'react';
import { CalendarDays, CheckCircle2, Clock3, XCircle, Send, Ban, ChevronLeft, ChevronRight } from 'lucide-react';
import {
  listLeaveBalances,
  listLeavePolicies,
  listLeaveRequests,
  listLeaveTypes,
  listPublicHolidays,
  createLeaveRequest,
  submitLeaveRequest,
  approveLeaveRequest,
  rejectLeaveRequest,
  cancelLeaveRequest,
} from '../api/leave';
import { useAuth } from '../context/AuthContext';
import LeaveConfiguration from '../components/LeaveConfiguration';

const formatDate = (value) => {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
};

const toArray = (value) => {
  if (Array.isArray(value)) return value;
  if (value && Array.isArray(value.results)) return value.results;
  return [];
};

const getStatusMeta = (status) => {
  switch (status) {
    case 'APPROVED':
      return { label: 'Approved', icon: CheckCircle2, tone: 'approved' };
    case 'REJECTED':
      return { label: 'Rejected', icon: XCircle, tone: 'rejected' };
    case 'PENDING':
    case 'SUBMITTED':
      return { label: 'Pending', icon: Clock3, tone: 'pending' };
    default:
      return { label: status || 'Draft', icon: CalendarDays, tone: 'neutral' };
  }
};

export default function LeaveManagement() {
  const { user } = useAuth();
  const membership = user?.memberships?.find((item) => item.organization_id === import.meta.env.VITE_ORGANIZATION_ID);
  const permissions = membership?.permissions || [];
  const canRequest = user?.is_system_admin || permissions.includes('leave.request');
  const canApprove = user?.is_system_admin || permissions.includes('leave.approve');
  const canManage = user?.is_system_admin || permissions.includes('leave.manage');
  const isEmployee = !user?.is_system_admin && !user?.is_hr_admin && !canManage;
  const [requests, setRequests] = useState([]);
  const [types, setTypes] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [balances, setBalances] = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({ leave_type: '', start_date: '', end_date: '', reason: '' });
  const [busy, setBusy] = useState(false);
  const [calendarMonth, setCalendarMonth] = useState(() => new Date());

  useEffect(() => {
    Promise.all([
      listLeaveRequests(),
      listLeaveTypes(),
      listLeavePolicies(),
      listLeaveBalances(),
      listPublicHolidays(),
    ])
      .then(([requestsData, typesData, policiesData, balancesData, holidaysData]) => {
        setRequests(toArray(requestsData));
        setTypes(toArray(typesData));
        setPolicies(toArray(policiesData));
        setBalances(toArray(balancesData));
        setHolidays(toArray(holidaysData));
      })
      .catch((err) => setError(err.message));
  }, []);

  const reloadRequests = async () => {
    const [requestsData, balanceData] = await Promise.all([listLeaveRequests(), listLeaveBalances()]);
    setRequests(toArray(requestsData)); setBalances(toArray(balanceData));
  };
  const reloadConfiguration = async () => {
    const [policyData, holidayData, balanceData] = await Promise.all([listLeavePolicies(), listPublicHolidays(), listLeaveBalances()]);
    setPolicies(toArray(policyData)); setHolidays(toArray(holidayData)); setBalances(toArray(balanceData));
  };

  const createDraft = async (event) => {
    event.preventDefault();
    setBusy(true); setError(''); setNotice('');
    try {
      await createLeaveRequest(form);
      setForm({ leave_type: '', start_date: '', end_date: '', reason: '' });
      await reloadRequests();
      setNotice('Leave request saved as a draft.');
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  const requestAction = async (action, request) => {
    setBusy(true); setError(''); setNotice('');
    try {
      if (action === 'submit') await submitLeaveRequest(request.id);
      if (action === 'approve') await approveLeaveRequest(request.id);
      if (action === 'reject') await rejectLeaveRequest(request.id);
      if (action === 'cancel') await cancelLeaveRequest(request.id);
      await reloadRequests();
      setNotice('Leave request updated.');
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  const stats = useMemo(() => {
    const pending = requests.filter((item) => ['PENDING', 'SUBMITTED'].includes(item.status)).length;
    const approved = requests.filter((item) => item.status === 'APPROVED').length;
    const rejected = requests.filter((item) => item.status === 'REJECTED').length;
    return { total: requests.length, pending, approved, rejected };
  }, [requests]);

  return (
    <div>
      <div className="page-heading">
        <div>
          <span className="eyebrow">Operations</span>
          <h2>Leave Management</h2>
          <p>{isEmployee ? 'View your leave balance, request time off, and track approval status.' : 'Track leave requests, balances, policies, and approvals across the organization.'}</p>
        </div>
      </div>

      {error && <div className="error banner">{error}</div>}
      {notice && <div className="success banner">{notice}</div>}
      <LeaveConfiguration types={types} policies={policies} canManage={canManage} isEmployee={isEmployee} onSaved={reloadConfiguration}/>

      {canRequest && <div className="panel">
        <div className="panel-head"><div><h3>{isEmployee ? 'Request time off' : 'Request leave'}</h3><p>{isEmployee ? 'Submit a leave request for manager or HR approval.' : 'Create a draft request for your internal leave workflow.'}</p></div></div>
        <form className="form-grid" onSubmit={createDraft}>
          <label className="field">Leave type<select value={form.leave_type} onChange={event => setForm({ ...form, leave_type: event.target.value })} required><option value="">Select leave type</option>{types.filter(type => type.is_active).map(type => <option key={type.id} value={type.id} disabled={!policies.some(policy => policy.leave_type === type.id && policy.is_active)}>{type.name}{policies.some(policy => policy.leave_type === type.id && policy.is_active) ? '' : ' — policy not configured'}</option>)}</select></label>
          <label className="field">Start date<input type="date" value={form.start_date} onChange={event => setForm({ ...form, start_date: event.target.value })} required /></label>
          <label className="field">End date<input type="date" value={form.end_date} onChange={event => setForm({ ...form, end_date: event.target.value })} required /></label>
          <label className="field wide">Reason<textarea value={form.reason} onChange={event => setForm({ ...form, reason: event.target.value })} rows="3" /></label>
          <div className="form-actions wide"><button className="primary" type="submit" disabled={busy}><CalendarDays size={16} /> Save draft</button></div>
        </form>
      </div>}

      <div className="stats">
        <div className="stat">
          <div className="stat-icon"><CalendarDays size={21} /></div>
          <div>
            <small>{isEmployee ? 'My requests' : 'Total requests'}</small>
            <strong>{stats.total}</strong>
          </div>
        </div>
        <div className="stat">
          <div className="stat-icon"><Clock3 size={21} /></div>
          <div>
            <small>Pending</small>
            <strong>{stats.pending}</strong>
          </div>
        </div>
        <div className="stat">
          <div className="stat-icon"><CheckCircle2 size={21} /></div>
          <div>
            <small>Approved</small>
            <strong>{stats.approved}</strong>
          </div>
        </div>
        <div className="stat">
          <div className="stat-icon"><XCircle size={21} /></div>
          <div>
            <small>Rejected</small>
            <strong>{stats.rejected}</strong>
          </div>
        </div>
      </div>

      <div className="panel" style={{ marginTop: '24px' }}>
        <div className="panel-head" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div><h3><CalendarDays size={18} /> {isEmployee ? 'My leave calendar' : 'Realtime Leave Calendar'}</h3><p>{isEmployee ? 'Your approved leave and public holidays appear here.' : 'Approved leave and public holidays appear on the calendar.'}</p></div>
          <div className="calendar-nav" aria-label="Calendar navigation"><button className="calendar-nav-button" type="button" aria-label="Previous month" title="Previous month" onClick={() => setCalendarMonth(current => new Date(current.getFullYear(), current.getMonth() - 1, 1))}><ChevronLeft size={18} /></button><button className="calendar-nav-button" type="button" aria-label="Next month" title="Next month" onClick={() => setCalendarMonth(current => new Date(current.getFullYear(), current.getMonth() + 1, 1))}><ChevronRight size={18} /></button></div>
        </div>
        <CalendarGrid month={calendarMonth} holidays={holidays} requests={requests} />
      </div>

      <div className="panel">
        <div className="panel-head">
          <div>
            <h3>Recent leave requests</h3>
            <p>{isEmployee ? 'Your latest leave submissions and review status.' : 'Latest submissions and review status.'}</p>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Type</th>
                <th>Period</th>
                <th>Leave days</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {requests.length ? requests.map((request) => {
                const meta = getStatusMeta(request.status);
                const Icon = meta.icon;
                return (
                  <tr key={request.id}>
                    <td><strong>{request.employee_name || 'Employee'}</strong></td>
                    <td>{request.leave_type_name || '—'}</td>
                    <td>{formatDate(request.start_date)} - {formatDate(request.end_date)}</td>
                    <td>{request.requested_days}</td>
                    <td>
                      <span className={`status ${meta.tone}`}>
                        <Icon size={14} /> {meta.label}
                      </span>
                    </td>
                    <td className="table-actions">
                      {canRequest && request.status === 'DRAFT' && <button className="link-button" type="button" disabled={busy} onClick={() => requestAction('submit', request)}><Send size={14} /> Submit</button>}
                      {canApprove && ['SUBMITTED', 'PENDING'].includes(request.status) && <><button className="link-button" type="button" disabled={busy} onClick={() => requestAction('approve', request)}><CheckCircle2 size={14} /> Approve</button><button className="link-button" type="button" disabled={busy} onClick={() => requestAction('reject', request)}><XCircle size={14} /> Reject</button></>}
                      {canRequest && ['DRAFT', 'SUBMITTED', 'PENDING'].includes(request.status) && <button className="link-button" type="button" disabled={busy} onClick={() => requestAction('cancel', request)}><Ban size={14} /> Cancel</button>}
                    </td>
                  </tr>
                );
              }) : (
                <tr>
                  <td colSpan="6" className="empty">No leave requests found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '18px', marginTop: '24px' }}>
        {false && <div className="panel">
          <div className="panel-head">
            <div>
              <h3>Leave types</h3>
            </div>
          </div>
          <div style={{ display: 'grid', gap: '10px' }}>
            {types.length ? types.map((item) => (
              <div key={item.id} style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px 12px' }}>
                <strong>{item.name}</strong>
                <div style={{ color: '#4b5563', fontSize: '12px', marginTop: '4px' }}>{item.code}</div>
                <div style={{ marginTop: '6px', fontSize: '12px' }}>{item.is_paid ? 'Paid' : 'Unpaid'} · {item.requires_approval ? 'Approval required' : 'No approval'} · {item.is_active ? 'Active' : 'Inactive'}</div>
              </div>
            )) : <p className="empty">No leave types available.</p>}
          </div>
        </div>}

        {false && <div className="panel">
          <div className="panel-head">
            <div>
              <h3>Leave policies</h3>
            </div>
          </div>
          <div style={{ display: 'grid', gap: '10px' }}>
            {policies.length ? policies.map((item) => (
              <div key={item.id} style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px 12px' }}>
                <strong>{item.leave_type_name || 'Policy'}</strong>
                <div style={{ fontSize: '12px', marginTop: '4px' }}>{item.days_per_year} days / year</div>
                <div style={{ fontSize: '12px', marginTop: '2px' }}>{item.is_active ? 'Active' : 'Inactive'} · Carry forward: {item.allow_carry_forward ? 'On' : 'Off'}</div>
              </div>
            )) : <p className="empty">No leave policies available.</p>}
          </div>
        </div>}

        <div className="panel">
          <div className="panel-head">
            <div>
              <h3><CalendarDays size={18} /> Public holidays</h3>
            </div>
          </div>
          <div style={{ display: 'grid', gap: '10px' }}>
            {holidays.length ? holidays.filter(item => item.is_active).map((item) => (
              <div key={item.id} style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px 12px' }}>
                <strong>{item.name || 'Holiday'}</strong>
                <div style={{ fontSize: '12px', marginTop: '4px' }}>{formatDate(item.date)}</div>
              </div>
            )) : <p className="empty">No public holidays configured.</p>}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '18px', marginTop: '24px' }}>
        {false && <div className="panel">
          <div className="panel-head">
            <div>
              <h3>Approval rules</h3>
            </div>
          </div>
          <div style={{ display: 'grid', gap: '10px' }}>
            {[].length ? [].slice(0, 6).map((item) => (
              <div key={item.id} style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px 12px' }}>
                <strong>{item.leave_type_name || 'Rule'}</strong>
                <div style={{ fontSize: '12px', marginTop: '4px' }}>Level {item.approval_level} · Min {item.minimum_days} days</div>
                <div style={{ fontSize: '12px', marginTop: '2px' }}>{item.is_active ? 'Active' : 'Inactive'}</div>
              </div>
            )) : <p className="empty">No approval rules configured.</p>}
          </div>
        </div>}

        <div className="panel">
          <div className="panel-head">
            <div>
              <h3><Clock3 size={18} /> Leave balances</h3>
            </div>
          </div>
          <div style={{ display: 'grid', gap: '10px' }}>
            {balances.length ? balances.map((item) => (
              <div key={item.id} style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px 12px' }}>
                <strong>{item.employee_name || 'Employee'}</strong>
                <div style={{ fontSize: '12px', marginTop: '4px' }}>{item.leave_type_name || 'Leave type'} · {item.year} · {Number(item.remaining_days || 0)} remaining</div>
                <div style={{ fontSize: '12px', marginTop: '2px' }}>Reserved in pending requests: {requests.filter(request => request.employee === item.employee && request.leave_type === item.leave_type && Number(request.start_date?.slice(0, 4)) === item.year && request.status === 'SUBMITTED').reduce((total, request) => total + Number(request.requested_days), 0)} days</div>
                <div style={{ fontSize: '12px', marginTop: '2px' }}>Used {Number(item.used_days || 0)} · Entitlement {Number(item.entitlement_days || 0)}</div>
              </div>
            )) : <p className="empty">No leave balances available.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}

function CalendarGrid({ month, holidays, requests }) {
  const first = new Date(month.getFullYear(), month.getMonth(), 1);
  const daysInMonth = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
  const offset = first.getDay();
  const cells = Array.from({ length: offset + daysInMonth }, (_, index) => index < offset ? null : new Date(month.getFullYear(), month.getMonth(), index - offset + 1));
  return <div className="leave-calendar">
    <h4 className="calendar-title">{month.toLocaleDateString([], { month: 'long', year: 'numeric' })}</h4>
    <div className="calendar-grid">
      {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => <strong className="calendar-weekday" key={day}>{day}</strong>)}
      {cells.map((date, index) => {
      if (!date) return <div key={`empty-${index}`} />;
      const key = [date.getFullYear(), date.getMonth() + 1, date.getDate()]
        .map(value => String(value).padStart(2, '0'))
        .join('-');
      const holiday = holidays.find(item => item.is_active && item.date === key);
      const leaveCount = requests.filter(item => item.status === 'APPROVED' && item.start_date <= key && item.end_date >= key).length;
      return <div className={`calendar-day${holiday ? ' holiday' : ''}${leaveCount ? ' has-leave' : ''}`} key={key}>
        <strong className="calendar-date">{date.getDate()}</strong>
        {holiday && <span className="calendar-holiday">{holiday.name}</span>}
        {leaveCount > 0 && <span className="calendar-leave">{leaveCount} on leave</span>}
      </div>;
      })}
    </div>
    <div className="calendar-legend"><span><i className="legend-swatch holiday" /> Public holiday</span><span><i className="legend-swatch leave" /> Approved leave</span></div>
  </div>;
}
