import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Clock3, Database, ShieldCheck } from 'lucide-react';
import { listAttendanceRecords } from '../api/attendance';

const formatTime = (value) => value ? new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—';
const statusLabel = (status) => (status || 'UNKNOWN').replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());

export default function Attendance() {
  const [records, setRecords] = useState([]);
  const [filter, setFilter] = useState('ALL');
  const [error, setError] = useState('');

  useEffect(() => {
    listAttendanceRecords()
      .then((data) => setRecords(Array.isArray(data) ? data : data?.results || []))
      .catch((err) => setError(err.message));
  }, []);

  const filtered = useMemo(() => (
    filter === 'ALL' ? records : records.filter((record) => record.status === filter)
  ), [filter, records]);
  const present = records.filter((record) => record.status === 'PRESENT').length;
  const exceptions = records.filter((record) => ['INCOMPLETE', 'ABSENT'].includes(record.status)).length;
  const late = records.filter((record) => Number(record.late_minutes) > 0).length;

  return (
    <div>
      <div className="page-heading">
        <div><span className="eyebrow">Time tracking</span><h2>Attendance</h2><p>Daily attendance records and exceptions.</p></div>
      </div>
      {error && <div className="error banner">{error}</div>}
      <div className="stats">
        <Stat icon={Clock3} label="Present" value={present} />
        <Stat icon={Database} label="Records" value={records.length} />
        <Stat icon={ShieldCheck} label="Exceptions" value={exceptions} />
        <Stat icon={AlertTriangle} label="Late arrivals" value={late} />
      </div>
      <div className="panel">
        <div className="toolbar">
          <select value={filter} onChange={(event) => setFilter(event.target.value)}>
            <option value="ALL">All statuses</option>
            {['PRESENT', 'ABSENT', 'INCOMPLETE', 'OFF_DAY', 'HOLIDAY', 'ON_LEAVE', 'EXCUSED'].map((status) => (
              <option key={status} value={status}>{statusLabel(status)}</option>
            ))}
          </select>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Employee</th><th>Date</th><th>Check-in</th><th>Check-out</th><th>Worked</th><th>Status</th></tr></thead>
            <tbody>
              {filtered.length ? filtered.map((record) => (
                <tr key={record.id}>
                  <td>{record.employee_name || record.employee_number || 'Employee'}</td>
                  <td>{record.attendance_date || '—'}</td>
                  <td>{formatTime(record.first_check_in_at)}</td>
                  <td>{formatTime(record.last_check_out_at)}</td>
                  <td>{record.worked_minutes == null ? '—' : `${Math.floor(record.worked_minutes / 60)}h ${record.worked_minutes % 60}m`}</td>
                  <td><span className={`status ${record.status === 'PRESENT' ? 'active' : record.status === 'ABSENT' ? 'inactive' : 'warning'}`}>{statusLabel(record.status)}</span></td>
                </tr>
              )) : <tr><td colSpan="6" className="empty">No attendance records found.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Stat({ icon: Icon, label, value }) {
  return <div className="stat"><div className="stat-icon"><Icon size={20} /></div><div><small>{label}</small><strong>{value}</strong></div></div>;
}
