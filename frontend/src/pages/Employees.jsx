import React, {useEffect, useMemo, useState} from 'react';
import {Link} from 'react-router-dom';
import {Edit3, Eye, Plus, Search, UserCheck, UserX} from 'lucide-react';
import {activateEmployee, deactivateEmployee, listEmployees} from '../api/employees';
import {useAuth} from '../context/AuthContext';

const employeeName = employee => [employee.identity?.first_name, employee.identity?.last_name].filter(Boolean).join(' ') || 'Unnamed employee';

export default function Employees() {
  const [employees, setEmployees] = useState([]);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('ALL');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const {user} = useAuth();
  const role = user?.role_code;
  const canCreate = user?.is_system_admin || ['ORGANIZATION_ADMIN', 'HR_MANAGER', 'HR_OFFICER'].includes(role);
  const canDeactivate = user?.is_system_admin || ['ORGANIZATION_ADMIN', 'HR_MANAGER'].includes(role);
  const canActivate = user?.is_system_admin || role === 'ORGANIZATION_ADMIN';

  const loadEmployees = async () => {
    setError('');
    try {
      setEmployees(await listEmployees());
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadEmployees(); }, []);

  const filteredEmployees = useMemo(() => employees.filter(employee => {
    const searchable = [employeeName(employee), employee.employee_number, employee.contact?.company_email, employee.assignment?.department_name, employee.assignment?.position_name].join(' ').toLowerCase();
    const matchesStatus = status === 'ALL' || (status === 'ACTIVE' ? employee.is_active : !employee.is_active);
    return searchable.includes(query.toLowerCase()) && matchesStatus;
  }), [employees, query, status]);

  const setEmployeeActive = async employee => {
    const action = employee.is_active ? deactivateEmployee : activateEmployee;
    const verb = employee.is_active ? 'Deactivate' : 'Reactivate';
    if (!window.confirm(`${verb} ${employeeName(employee)}?`)) return;
    try {
      await action(employee.id);
      await loadEmployees();
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  return <div>
    <div className="page-heading">
      <div><span className="eyebrow">People</span><h2>Employees</h2><p>View and manage employee records.</p></div>
      {canCreate && <Link className="primary" to="/employees/new"><Plus size={18}/> Add employee</Link>}
    </div>
    {error && <div className="error banner" role="alert">{error}</div>}
    <div className="toolbar">
      <label className="search"><Search size={18}/><input aria-label="Search employees" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search name, ID, department"/></label>
      <select aria-label="Filter by status" value={status} onChange={event => setStatus(event.target.value)}>
        <option value="ALL">All statuses</option><option value="ACTIVE">Active</option><option value="INACTIVE">Inactive</option>
      </select>
    </div>
    <div className="panel"><div className="table-wrap"><table>
      <thead><tr><th>Employee</th><th>ID</th><th>Department</th><th>Position</th><th>Employment</th><th>Status</th><th>Actions</th></tr></thead>
      <tbody>
        {filteredEmployees.map(employee => <tr key={employee.id}>
          <td><Link className="employee-name" to={`/employees/${employee.id}`}>{employeeName(employee)}</Link><small>{employee.contact?.company_email || employee.contact?.personal_email || '—'}</small></td>
          <td>{employee.employee_number || '—'}</td><td>{employee.assignment?.department_name || '—'}</td><td>{employee.assignment?.position_name || '—'}</td><td>{employee.employment?.employment_type || '—'}</td>
          <td><span className={employee.is_active ? 'status active' : 'status inactive'}>{employee.is_active ? 'Active' : 'Inactive'}</span></td>
          <td><div className="row-actions"><Link className="link-button" to={`/employees/${employee.id}`} aria-label={`View ${employeeName(employee)}`} title="View"><Eye size={16}/></Link>{canCreate && <Link className="link-button" to={`/employees/${employee.id}/edit`} aria-label={`Edit ${employeeName(employee)}`} title="Edit"><Edit3 size={16}/></Link>}{((employee.is_active && canDeactivate) || (!employee.is_active && canActivate)) && <button className="link-button" type="button" onClick={() => setEmployeeActive(employee)} title={employee.is_active ? 'Deactivate' : 'Reactivate'} aria-label={`${employee.is_active ? 'Deactivate' : 'Reactivate'} ${employeeName(employee)}`}>{employee.is_active ? <UserX size={16}/> : <UserCheck size={16}/>}</button>}</div></td>
        </tr>)}
        {!loading && !filteredEmployees.length && <tr><td colSpan="7" className="empty">{error ? 'Employee records could not be loaded.' : 'No employees match this view.'}</td></tr>}
        {loading && <tr><td colSpan="7" className="empty">Loading employees…</td></tr>}
      </tbody>
    </table></div></div>
  </div>;
}
