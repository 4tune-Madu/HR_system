import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Clock3, Database, ShieldCheck, RefreshCw, UserPlus, BadgeCheck, CheckCircle2, TimerReset, CalendarClock, UsersRound, Pencil, Power } from 'lucide-react';
import { listAttendanceRecords, listAttendanceDevices, listAttendanceSyncLogs, createAttendanceDevice, updateAttendanceDevice, getDeviceUsers, getDeviceMappings, createDeviceMapping, deleteDeviceMapping, manualCheckIn, syncDevice, reconcileAttendanceRecord } from '../api/attendance';
import { listEmployees } from '../api/employees';
import { useAuth } from '../context/AuthContext';

const formatTime = (value) => value ? new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—';
const attendanceStatus = (record) => {
  if (record.status === 'PRESENT' && Number(record.late_minutes) >= 60) return 'OVERLATE';
  if (record.status === 'PRESENT' && Number(record.late_minutes) > 0) return 'LATE';
  return record.status;
};
const statusLabel = (status) => (status || 'UNKNOWN').replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());

export default function Attendance() {
  const { user } = useAuth();
  const isSystemAdmin = user?.is_system_admin;
  const membership = user?.memberships?.find((item) => item.organization_id === import.meta.env.VITE_ORGANIZATION_ID);
  const permissions = membership?.permissions || [];
  const has = (permission) => user?.is_system_admin || permissions.includes(permission);
  const isEmployee = !isSystemAdmin && !user?.is_hr_admin && !has('employee.view');
  const canViewEmployeeHistory = isSystemAdmin || user?.is_hr_admin || has('employee.view');
  const canViewDevices = isSystemAdmin && has('attendance.device.view');
  const canManageDevices = isSystemAdmin && has('attendance.device.manage');
  const canManageManual = isSystemAdmin && has('attendance.manual.manage');
  const canReconcile = isSystemAdmin && has('attendance.reconciliation.manage');
  const [records, setRecords] = useState([]);
  const [historyEmployeeId, setHistoryEmployeeId] = useState('');
  const [syncLogs, setSyncLogs] = useState([]);
  const [filter, setFilter] = useState('ALL');
  const [error, setError] = useState('');
  const [deviceId, setDeviceId] = useState('');
  const [devices, setDevices] = useState([]);
  const [showDeviceForm, setShowDeviceForm] = useState(true);
  const [deviceForm, setDeviceForm] = useState({ name: '', vendor: '', model: '', serial_number: '', connection_type: 'NETWORK', ip_address: '', port: '4370' });
  const [editingDevice, setEditingDevice] = useState(null);
  const [deviceUsers, setDeviceUsers] = useState([]);
  const [mappings, setMappings] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [deviceNotice, setDeviceNotice] = useState('');
  const [deviceLoading, setDeviceLoading] = useState(false);
  const [mappingForm, setMappingForm] = useState({ device_user_id: '', employee_id: '', display_name: '' });
  const [manualForm, setManualForm] = useState({ employee_id: '', occurred_at: '' });
  const [syncForm, setSyncForm] = useState({ start_date: '', end_date: '' });

  useEffect(() => {
    listAttendanceRecords()
      .then((data) => setRecords(Array.isArray(data) ? data : data?.results || []))
      .catch((err) => setError(err.message));

    listEmployees()
      .then((data) => setEmployees(Array.isArray(data) ? data : data?.results || []))
      .catch(() => setEmployees([]));

    if (canViewDevices) listAttendanceDevices()
      .then((data) => {
        const nextDevices = Array.isArray(data) ? data : data?.results || [];
        setDevices(nextDevices);
        setShowDeviceForm(!nextDevices.length);
        if (nextDevices.length) setDeviceId((current) => current || nextDevices[0].id);
      })
      .catch((err) => setDeviceNotice(err.message));

    if (canViewDevices) listAttendanceSyncLogs()
      .then((data) => setSyncLogs(Array.isArray(data) ? data : data?.results || []))
      .catch(() => setSyncLogs([]));
  }, [canViewDevices]);

  useEffect(() => {
    if (!canViewDevices || !deviceId) {
      setDeviceUsers([]);
      setMappings([]);
      return;
    }
    loadDeviceState();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canViewDevices, deviceId]);

  const loadDeviceState = async () => {
    if (!deviceId) return;
    setDeviceLoading(true);
    setDeviceNotice('');
    try {
      const [users, deviceMappings] = await Promise.all([
        getDeviceUsers(deviceId),
        getDeviceMappings(deviceId),
      ]);
      setDeviceUsers(Array.isArray(users) ? users : users?.results || []);
      setMappings(Array.isArray(deviceMappings) ? deviceMappings : deviceMappings?.results || []);
    } catch (err) {
      setDeviceNotice(err.message);
      setDeviceUsers([]);
      setMappings([]);
    } finally {
      setDeviceLoading(false);
    }
  };

  const resetDeviceForm = () => {
    setEditingDevice(null);
    setShowDeviceForm(false);
    setDeviceForm({ name: '', vendor: '', model: '', serial_number: '', connection_type: 'NETWORK', ip_address: '', port: '4370' });
  };

  const handleDeviceSubmit = async (event) => {
    event.preventDefault();
    try {
      const payload = { ...deviceForm, port: deviceForm.port ? Number(deviceForm.port) : null, ip_address: deviceForm.ip_address || null };
      const saved = editingDevice ? await updateAttendanceDevice(editingDevice.id, payload) : await createAttendanceDevice(payload);
      setDevices((current) => editingDevice ? current.map((device) => device.id === saved.id ? saved : device) : [...current, saved].sort((a, b) => a.name.localeCompare(b.name)));
      setDeviceId(saved.id);
      setDeviceNotice(editingDevice ? 'Attendance device updated.' : 'Attendance device registered.');
      resetDeviceForm();
    } catch (err) {
      setDeviceNotice(err.message);
    }
  };

  const editDevice = (device) => {
    if (!device) return;
    setEditingDevice(device);
    setShowDeviceForm(true);
    setDeviceForm({ name: device.name || '', vendor: device.vendor || '', model: device.model || '', serial_number: device.serial_number || '', connection_type: device.connection_type || 'NETWORK', ip_address: device.ip_address || '', port: device.port ? String(device.port) : '' });
  };

  const toggleDevice = async () => {
    const device = devices.find((item) => item.id === deviceId);
    if (!device) return;
    try {
      const saved = await updateAttendanceDevice(device.id, { is_active: !device.is_active });
      setDevices((current) => current.map((item) => item.id === saved.id ? saved : item));
      setDeviceNotice(saved.is_active ? 'Attendance device activated.' : 'Attendance device deactivated.');
    } catch (err) {
      setDeviceNotice(err.message);
    }
  };

  const handleMapUser = async (event) => {
    event.preventDefault();
    if (!deviceId || !mappingForm.device_user_id || !mappingForm.employee_id) {
      setDeviceNotice('Please provide a device user ID and employee.');
      return;
    }

    try {
      await createDeviceMapping(deviceId, {
        device_user_id: mappingForm.device_user_id,
        employee_id: mappingForm.employee_id,
        display_name: mappingForm.display_name,
      });
      setDeviceNotice('Device user mapped successfully.');
      setMappingForm({ device_user_id: '', employee_id: '', display_name: '' });
      loadDeviceState();
    } catch (err) {
      setDeviceNotice(err.message);
    }
  };

  const handleDeleteMapping = async (deviceUserId) => {
    try {
      await deleteDeviceMapping(deviceId, deviceUserId);
      setDeviceNotice('Mapping removed successfully.');
      loadDeviceState();
    } catch (err) {
      setDeviceNotice(err.message);
    }
  };

  const handleManualCheckIn = async (event) => {
    event.preventDefault();
    try {
      await manualCheckIn({
        employee_id: manualForm.employee_id,
        occurred_at: manualForm.occurred_at || null,
      });
      setDeviceNotice('Manual attendance check-in submitted.');
      setManualForm({ employee_id: '', occurred_at: '' });
      listAttendanceRecords()
        .then((data) => setRecords(Array.isArray(data) ? data : data?.results || []))
        .catch((err) => setError(err.message));
    } catch (err) {
      setDeviceNotice(err.message);
    }
  };

  const handleSync = async () => {
    if (!deviceId) {
      setDeviceNotice('Enter a device ID before syncing.');
      return;
    }

    try {
      const result = await syncDevice(deviceId, {
        start_date: syncForm.start_date || undefined,
        end_date: syncForm.end_date || undefined,
      });
      setDeviceNotice(`Sync started successfully: ${result?.status || 'queued'}`);
      const logs = await listAttendanceSyncLogs(deviceId);
      setSyncLogs(Array.isArray(logs) ? logs : logs?.results || []);
    } catch (err) {
      setDeviceNotice(err.message);
    }
  };

  const handleReconcile = async (recordId) => {
    try {
      const updated = await reconcileAttendanceRecord(recordId);
      setRecords((current) => current.map((record) => record.id === updated.id ? updated : record));
      setDeviceNotice('Attendance record reconciled successfully.');
    } catch (err) {
      setDeviceNotice(err.message);
    }
  };

  const today = new Date();
  const todayKey = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  const dailySnapshot = useMemo(() => {
    const todayRecords = records.filter((record) => String(record.attendance_date || record.date || '').slice(0, 10) === todayKey);
    const roster = isEmployee ? [{
      id: user.employee_id,
      is_active: true,
      identity: { first_name: user.first_name, last_name: user.last_name },
    }] : employees.filter((employee) => employee.is_active);
    return roster.map((employee) => {
      const employeeName = [employee.identity?.first_name, employee.identity?.last_name].filter(Boolean).join(' ') || 'Unnamed employee';
      const record = todayRecords.find((item) => String(item.employee_id || item.employee || '') === String(employee.id) || item.employee_name === employeeName);
      return record || {
        id: `absent-${employee.id}`,
        employee_id: employee.id,
        employee_name: employeeName,
        attendance_date: todayKey,
        status: 'ABSENT',
        first_check_in_at: null,
        is_synthetic: true,
      };
    });
  }, [employees, isEmployee, records, todayKey, user]);
  const historyRows = useMemo(() => {
    const employeeId = isEmployee ? user?.employee_id : historyEmployeeId;
    if (!employeeId) return [];
    return records
      .filter((record) => String(record.employee_id || record.employee || '') === String(employeeId))
      .sort((a, b) => String(b.attendance_date || '').localeCompare(String(a.attendance_date || '')));
  }, [historyEmployeeId, isEmployee, records, user]);
  const filtered = useMemo(() => (
    filter === 'ALL' ? dailySnapshot : dailySnapshot.filter((record) => attendanceStatus(record) === filter)
  ), [dailySnapshot, filter]);

  const unmappedEmployees = useMemo(() => {
    const mappedEmployeeIds = new Set(mappings.map((mapping) => mapping.employee || mapping.employee_id));
    return employees.filter((employee) => employee.is_active && !mappedEmployeeIds.has(employee.id));
  }, [employees, mappings]);

  const summary = useMemo(() => {
    const total = dailySnapshot.length;
    const present = dailySnapshot.filter((record) => attendanceStatus(record) === 'PRESENT').length;
    const absences = dailySnapshot.filter((record) => record.status === 'ABSENT').length;
    const late = dailySnapshot.filter((record) => ['LATE', 'OVERLATE'].includes(attendanceStatus(record))).length;
    const overlate = dailySnapshot.filter((record) => attendanceStatus(record) === 'OVERLATE').length;
    const onLeave = dailySnapshot.filter((record) => attendanceStatus(record) === 'ON_LEAVE').length;
    const holidays = dailySnapshot.filter((record) => attendanceStatus(record) === 'HOLIDAY').length;
    const exceptions = dailySnapshot.filter((record) => attendanceStatus(record) === 'ABSENT').length;
    return { total, present, absences, late, overlate, onLeave, holidays, exceptions };
  }, [dailySnapshot]);

  const compliance = summary.total ? Math.round((summary.present / summary.total) * 100) : 0;
  const selectedHistoryEmployee = employees.find((employee) => String(employee.id) === String(historyEmployeeId));

  return (
    <div className="attendance-shell">
      <div className="page-heading attendance-header">
        <div>
          <span className="eyebrow">Time tracking</span>
          <h2>Attendance day</h2>
          <p>{isSystemAdmin ? 'Daily attendance summary, status compliance, and device operations.' : 'Daily attendance, approved leave, and public holiday status.'}</p>
        </div>
        <div className="today-pill">
          <CalendarClock size={18} />
          {new Date().toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })}
        </div>
      </div>

      {error && <div className="error banner">{error}</div>}

      <div className="stats attendance-stats">
        <Stat icon={CheckCircle2} label="Present" value={summary.present} />
        <Stat icon={TimerReset} label="Late" value={summary.late} />
        <Stat icon={AlertTriangle} label="Overlate" value={summary.overlate} />
        <Stat icon={AlertTriangle} label="Absent" value={summary.absences} />
        <Stat icon={CalendarClock} label="On leave" value={summary.onLeave} />
        <Stat icon={UsersRound} label="Records" value={summary.total} />
      </div>

      <div className="attendance-layout">
        <div className="panel attendance-focus">
          <div className="panel-head">
            <div>
              <h3>Daily attendance overview</h3>
              <p>Compliance and operational status for the current attendance day.</p>
            </div>
          </div>

          <div className="compliance-card">
            <div className="compliance-badge">{compliance}%</div>
            <div>
              <strong>Attendance compliance</strong>
              <small>{summary.present} of {summary.total} employees marked present</small>
            </div>
          </div>

          <div className="bars">
            <Bar label="Present" count={summary.present} total={summary.total} tone="present" />
            <Bar label="Late" count={summary.late} total={summary.total} tone="late" />
            <Bar label="Absent" count={summary.absences} total={summary.total} tone="absent" />
            <Bar label="Exceptions" count={summary.exceptions} total={summary.total} tone="alert" />
          </div>
        </div>

        <div className="panel attendance-quick-actions">
          <div className="panel-head">
            <div>
              <h3>Quick actions</h3>
              <p>Manage the day’s staffing flow.</p>
            </div>
          </div>

          <div className="quick-list">
            <QuickItem icon={UsersRound} title="Checked in" value={`${summary.present} records`} tone="success" />
            <QuickItem icon={CalendarClock} title="Leave sync" value={`${summary.onLeave} on leave`} tone="neutral" />
            {isSystemAdmin && <QuickItem icon={Database} title="Device sync" value="Ready" tone="neutral" />}
            <QuickItem icon={ShieldCheck} title="Exceptions" value={`${summary.exceptions} flagged`} tone="warning" />
          </div>
        </div>
      </div>

      <div className="panel table-panel">
        <div className="toolbar">
          <div>
            <h3>Attendance snapshot</h3>
            <p>Daily status for active employees; employees without a punch are shown as absent.</p>
          </div>
          <select value={filter} onChange={(event) => setFilter(event.target.value)}>
            <option value="ALL">All statuses</option>
            {['PRESENT', 'LATE', 'OVERLATE', 'ABSENT', 'HOLIDAY', 'ON_LEAVE'].map((status) => (
              <option key={status} value={status}>{statusLabel(status)}</option>
            ))}
          </select>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Date</th>
                <th>Check-in</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length ? filtered.map((record) => (
                <tr key={record.id}>
                  <td>
                    <strong>{record.employee_name || record.employee_number || 'Employee'}</strong>
                  </td>
                  <td>{record.attendance_date || '—'}</td>
                  <td>{record.is_synthetic ? 'No punch recorded' : formatTime(record.first_check_in_at)}</td>
                  <td>
                    <span className={`status ${attendanceStatus(record) === 'PRESENT' ? 'active' : record.status === 'ABSENT' ? 'inactive' : 'warning'}`}>{statusLabel(attendanceStatus(record))}</span>
                  </td>
                </tr>
              )) : <tr><td colSpan="4" className="empty">No active employees found for this day.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel table-panel attendance-history-panel">
        <div className="toolbar">
          <div>
            <h3>{isEmployee ? 'My attendance history' : 'Employee attendance history'}</h3>
            <p>{isEmployee ? 'Review your recorded check-ins and attendance status.' : 'Select an employee to review their recorded attendance.'}</p>
          </div>
          {canViewEmployeeHistory && <select value={historyEmployeeId} onChange={(event) => setHistoryEmployeeId(event.target.value)} aria-label="Employee attendance history">
            <option value="">Select employee</option>
            {employees.filter((employee) => employee.is_active).map((employee) => <option key={employee.id} value={employee.id}>{employee.identity?.first_name || employee.employee_number || 'Employee'} {employee.identity?.last_name || ''}</option>)}
          </select>}
        </div>
        {canViewEmployeeHistory && !historyEmployeeId ? <p className="empty">Choose an employee to view attendance history.</p> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Employee</th><th>Check-in</th><th>Check-out</th><th>Status</th><th>Worked</th></tr></thead>
              <tbody>
                {historyRows.length ? historyRows.map((record) => <tr key={record.id}>
                  <td>{record.attendance_date || '—'}</td>
                  <td><strong>{record.employee_name || selectedHistoryEmployee?.employee_number || 'Employee'}</strong></td>
                  <td>{formatTime(record.first_check_in_at)}</td>
                  <td>{formatTime(record.last_check_out_at)}</td>
                  <td><span className={`status ${attendanceStatus(record) === 'PRESENT' ? 'active' : 'warning'}`}>{statusLabel(attendanceStatus(record))}</span></td>
                  <td>{record.worked_minutes == null ? '—' : `${record.worked_minutes} mins`}</td>
                </tr>) : <tr><td colSpan="6" className="empty">No attendance records found for this employee.</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {isSystemAdmin && <div className="panel device-panel">
        <div className="device-header">
          <div>
            <span className="eyebrow">Device operations</span>
            <h3>Attendance device management</h3>
          </div>
          <div className="device-search">
              <select className="device-select" aria-label="Registered attendance device" value={deviceId} onChange={(event) => setDeviceId(event.target.value)}>
                <option value="">Select registered device</option>
                {devices.map((device) => <option key={device.id} value={device.id}>{device.name}{device.is_active ? '' : ' (inactive)'}</option>)}
              </select>
              <button className="device-control device-load" onClick={loadDeviceState} type="button">
                <RefreshCw size={16} /> Load device
              </button>
              {deviceId && canManageDevices && <button className="device-control device-edit" type="button" onClick={() => editDevice(devices.find((device) => device.id === deviceId))}><Pencil size={15} /> Edit</button>}
              {deviceId && canManageDevices && <button className={`device-control ${devices.find((device) => device.id === deviceId)?.is_active ? 'device-deactivate' : 'device-activate'}`} type="button" onClick={toggleDevice}><Power size={15} />{devices.find((device) => device.id === deviceId)?.is_active ? 'Deactivate' : 'Activate'}</button>}
          </div>
        </div>

        {deviceId && unmappedEmployees.length > 0 && <div className="attendance-mapping-alert" role="status"><AlertTriangle size={18} /><div><strong>Attendance mapping needed</strong><p>{unmappedEmployees.length} active employee{unmappedEmployees.length === 1 ? '' : 's'} {unmappedEmployees.length === 1 ? 'is' : 'are'} not mapped to this device. Map new employees before their attendance can be matched.</p></div></div>}
        {deviceNotice && <div className="info banner" style={{ marginTop: '16px' }}>{deviceNotice}</div>}

        {canManageDevices && showDeviceForm && <form className="device-action" onSubmit={handleDeviceSubmit} style={{ marginTop: '16px' }}>
          <h4>{editingDevice ? 'Edit registered device' : 'Register attendance device'}</h4>
          <input required value={deviceForm.name} onChange={(event) => setDeviceForm({ ...deviceForm, name: event.target.value })} placeholder="Device name" />
          <input value={deviceForm.vendor} onChange={(event) => setDeviceForm({ ...deviceForm, vendor: event.target.value })} placeholder="Vendor" />
          <input value={deviceForm.model} onChange={(event) => setDeviceForm({ ...deviceForm, model: event.target.value })} placeholder="Model" />
          <input value={deviceForm.serial_number} onChange={(event) => setDeviceForm({ ...deviceForm, serial_number: event.target.value })} placeholder="Serial number" />
          <select value={deviceForm.connection_type} onChange={(event) => setDeviceForm({ ...deviceForm, connection_type: event.target.value })}>
            {['NETWORK', 'ADMS', 'USB', 'FILE', 'API', 'OTHER'].map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
          {deviceForm.connection_type === 'NETWORK' && <>
            <input required value={deviceForm.ip_address} onChange={(event) => setDeviceForm({ ...deviceForm, ip_address: event.target.value })} placeholder="IP address" />
            <input required type="number" min="1" value={deviceForm.port} onChange={(event) => setDeviceForm({ ...deviceForm, port: event.target.value })} placeholder="Port" />
          </>}
          <button className="primary" type="submit">{editingDevice ? 'Save device' : 'Register device'}</button>
          {editingDevice && <button type="button" onClick={resetDeviceForm}>Cancel</button>}
        </form>}

        {deviceLoading ? <p>Loading device data…</p> : (
          <div className="device-grid">
            <div className="device-card">
              <h4>Mapped device users</h4>
              {deviceUsers.length ? (
                <ul>
                  {deviceUsers.map((user) => (
                    <li key={user.user_id}>
                      <div><strong>{user.name || 'Unknown user'}</strong></div>
                      <small>User ID: {user.user_id}</small>
                      <span className={user.mapped ? 'pill success' : 'pill warning'}>{user.mapped ? 'Mapped' : 'Not mapped'}</span>
                    </li>
                  ))}
                </ul>
              ) : <p className="empty">No device users loaded.</p>}
            </div>

            <div className="device-card">
              <h4>Current mappings</h4>
              {mappings.length ? (
                <ul>
                  {mappings.map((mapping) => (
                    <li key={`${mapping.device_user_id}-${mapping.employee}`}>
                      <div><strong>{mapping.employee_name || mapping.display_name || mapping.device_user_id}</strong></div>
                      <small>Device user: {mapping.device_user_id}</small>
                      {canManageDevices && <button className="link-button" type="button" onClick={() => handleDeleteMapping(mapping.device_user_id)}>Remove</button>}
                    </li>
                  ))}
                </ul>
              ) : <p className="empty">No mappings configured.</p>}
            </div>
          </div>
        )}

          <div className="device-grid actions-grid">
          {canManageDevices && <form className="device-action" onSubmit={handleMapUser}>
            <h4><UserPlus size={16} /> Map device user</h4>
            <input value={mappingForm.device_user_id} onChange={(event) => setMappingForm({ ...mappingForm, device_user_id: event.target.value })} placeholder="Device user ID" />
            <select value={mappingForm.employee_id} onChange={(event) => setMappingForm({ ...mappingForm, employee_id: event.target.value })}>
              <option value="">Select employee</option>
              {employees.map((employee) => (
                <option key={employee.id} value={employee.id}>{employee.identity?.first_name || employee.employee_number || 'Employee'} {employee.identity?.last_name || ''}</option>
              ))}
            </select>
            <input value={mappingForm.display_name} onChange={(event) => setMappingForm({ ...mappingForm, display_name: event.target.value })} placeholder="Display name (optional)" />
            <button className="primary" type="submit">Map employee</button>
          </form>}

          {canManageManual && <form className="device-action" onSubmit={handleManualCheckIn}>
            <h4><BadgeCheck size={16} /> Manual check-in</h4>
            <select value={manualForm.employee_id} onChange={(event) => setManualForm({ ...manualForm, employee_id: event.target.value })}>
              <option value="">Select employee</option>
              {employees.map((employee) => (
                <option key={employee.id} value={employee.id}>{employee.identity?.first_name || employee.employee_number || 'Employee'} {employee.identity?.last_name || ''}</option>
              ))}
            </select>
            <input type="datetime-local" value={manualForm.occurred_at} onChange={(event) => setManualForm({ ...manualForm, occurred_at: event.target.value })} />
            <button className="primary" type="submit">Submit manual check-in</button>
          </form>}

          {canManageDevices && <div className="device-action device-sync-box">
            <h4><RefreshCw size={16} /> Device sync</h4>
            <input type="date" value={syncForm.start_date} onChange={(event) => setSyncForm({ ...syncForm, start_date: event.target.value })} />
            <input type="date" value={syncForm.end_date} onChange={(event) => setSyncForm({ ...syncForm, end_date: event.target.value })} />
            <button className="primary" type="button" onClick={handleSync}>Sync device</button>
          </div>}

          <div className="device-card" style={{ marginTop: '16px' }}>
            <h4>Recent sync history</h4>
            {syncLogs.length ? <div className="table-wrap"><table><thead><tr><th>Device</th><th>Started</th><th>Status</th><th>Read</th><th>Created</th><th>Duplicates</th><th>Unresolved</th><th>Invalid</th></tr></thead><tbody>
              {syncLogs.slice(0, 10).map((log) => <tr key={log.id}><td>{log.device_name || 'Unknown device'}</td><td>{log.started_at ? new Date(log.started_at).toLocaleString() : '—'}</td><td><span className={`status ${log.status === 'SUCCESS' ? 'active' : log.status === 'FAILED' ? 'inactive' : 'warning'}`}>{statusLabel(log.status)}</span></td><td>{log.records_read}</td><td>{log.created}</td><td>{log.duplicates}</td><td>{log.unresolved}</td><td>{log.invalid}</td></tr>)}
            </tbody></table></div> : <p className="empty">No synchronization history yet.</p>}
          </div>
        </div>
      </div>}
    </div>
  );
}

function Stat({ icon: Icon, label, value }) {
  return (
    <div className="stat attendance-stat">
      <div className="stat-icon"><Icon size={20} /></div>
      <div>
        <small>{label}</small>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

function Bar({ label, count, total, tone }) {
  const percent = total ? Math.max(0, (count / total) * 100) : 0;
  return (
    <div className="bar-row">
      <div className="bar-head">
        <span>{label}</span>
        <strong>{count}</strong>
      </div>
      <div className="bar-track">
        <span className={`bar-fill ${tone}`} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

function QuickItem({ icon: Icon, title, value, tone }) {
  return (
    <div className={`quick-item ${tone}`}>
      <div className="quick-icon"><Icon size={18} /></div>
      <div>
        <small>{title}</small>
        <strong>{value}</strong>
      </div>
    </div>
  );
}
