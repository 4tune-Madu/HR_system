import React, { useEffect, useMemo, useState } from 'react';
import { CalendarDays, CheckCircle2, Clock3, XCircle } from 'lucide-react';
import { listLeaveRequests } from '../api/leave';

const formatDate = (value) => {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
};

const statusMeta = (status) => {
  switch (status) {
    case 'APPROVED': return { label: 'Approved', icon: CheckCircle2, tone: 'active' };
    case 'REJECTED': return { label: 'Rejected', icon: XCircle, tone: 'inactive' };
    case 'PENDING':
    case 'SUBMITTED': return { label: 'Pending', icon: Clock3, tone: 'warning' };
    default: return { label: status || 'Draft', icon: CalendarDays, tone: '' };
  }
};

export default function LeaveManagement() {
  const [requests, setRequests] = useState([]);
  const [filter, setFilter] = useState('ALL');
  const [error, setError] = useState('');

  useEffect(() => {
    listLeaveRequests()
      .then((data) => setRequests(Array.isArray(data) ? data : data?.results || []))
      .catch((err) => setError(err.message));
  }, []);

  const filtered = useMemo(() => (
    filter === 'ALL' ? requests : requests.filter((item) => item.status === filter)
  ), [filter, requests]);
  const pending = requests.filter((item) => ['PENDING', 'SUBMITTED'].includes(item.status)).length;
  const approved = requests.filter((item) => item.status === 'APPROVED').length;
  const rejected = requests.filter((item) => item.status === 'REJECTED').length;

  return (
    <div>
      <div className="page-heading">
        <div>
          <span className="eyebrow">Operations</span>
          <h2>Leave Management</h2>
          <p>Track leave requests and approvals across the organization.</p>
        </div>
      </div>
      {error && <div className="error banner">{error}</div>}
      <div className="stats">
        <Stat icon={CalendarDays} label="Total requests" value={requests.length} />
        <Stat icon={Clock3} label="Pending" value={pending} />
        <Stat icon={CheckCircle2} label="Approved" value={approved} />
        <Stat icon={XCircle} label="Rejected" value={rejected} />
      </div>
      <div className="panel">
        <div className="toolbar">
          <select value={filter} onChange={(event) => setFilter(event.target.value)}>
            <option value="ALL">All statuses</option>
            <option value="PENDING">Pending</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Employee</th><th>Type</th><th>Period</th><th>Days</th><th>Status</th></tr></thead>
            <tbody>
              {filtered.length ? filtered.slice(0, 8).map((request) => {
                const meta = statusMeta(request.status);
                const Icon = meta.icon;
                return (
                  <tr key={request.id}>
                    <td>{request.employee_name || 'Employee'}</td>
                    <td>{request.leave_type_name || '—'}</td>
                    <td>{formatDate(request.start_date)} - {formatDate(request.end_date)}</td>
                    <td>{request.requested_days ?? '—'}</td>
                    <td><span className={`status ${meta.tone}`}><Icon size={14} /> {meta.label}</span></td>
                  </tr>
                );
              }) : <tr><td colSpan="5" className="empty">No leave requests found.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Stat({ icon: Icon, label, value }) {
  return <div className="stat"><div className="stat-icon"><Icon size={21} /></div><div><small>{label}</small><strong>{value}</strong></div></div>;
}
