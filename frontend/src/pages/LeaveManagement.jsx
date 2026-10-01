import React, { useEffect, useMemo, useState } from 'react';
import { CalendarDays, CheckCircle2, Clock3, XCircle } from 'lucide-react';
import { listLeaveRequests } from '../api/leave';

const formatDate = (value) => {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
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
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    listLeaveRequests()
      .then((data) => setRequests(Array.isArray(data) ? data : []))
      .catch((err) => setError(err.message));
  }, []);

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
          <p>Track leave requests and approvals across the organization.</p>
        </div>
      </div>

      {error && <div className="error banner">{error}</div>}

      <div className="stats">
        <div className="stat">
          <div className="stat-icon"><CalendarDays size={21} /></div>
          <div>
            <small>Total requests</small>
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

      <div className="panel">
        <div className="panel-head">
          <div>
            <h3>Recent leave requests</h3>
            <p>Latest submissions and review status.</p>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Type</th>
                <th>Period</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {requests.length ? requests.slice(0, 8).map((request) => {
                const meta = getStatusMeta(request.status);
                const Icon = meta.icon;
                return (
                  <tr key={request.id}>
                    <td>
                      <strong>{request.employee_name || 'Employee'}</strong>
                    </td>
                    <td>{request.leave_type_name || '—'}</td>
                    <td>{formatDate(request.start_date)} - {formatDate(request.end_date)}</td>
                    <td>
                      <span className={`status ${meta.tone}`}>
                        <Icon size={14} /> {meta.label}
                      </span>
                    </td>
                  </tr>
                );
              }) : (
                <tr>
                  <td colSpan="4" className="empty">No leave requests found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
