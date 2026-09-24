import React, {useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import {Plus} from 'lucide-react';
import {listEmployees} from '../api/employees';

export default function Employees() {
  const [employees, setEmployees] = useState([]);
  const [error, setError] = useState('');
  useEffect(() => { listEmployees().then(setEmployees).catch(error => setError(error.message)); }, []);
  return <div><div className="page-heading"><div><span className="eyebrow">People</span><h2>Employees</h2><p>View and manage employee records.</p></div><Link className="primary" to="/employees/new"><Plus size={18}/> Add employee</Link></div>{error && <div className="error banner">{error}</div>}<div className="panel"><div className="table-wrap"><table><thead><tr><th>Employee</th><th>ID</th><th>Status</th></tr></thead><tbody>{employees.map(employee => <tr key={employee.id}><td><Link className="employee-name" to={`/employees/${employee.id}`}>{[employee.identity?.first_name, employee.identity?.last_name].filter(Boolean).join(' ') || 'Unnamed employee'}</Link></td><td>{employee.employee_number || '—'}</td><td>{employee.is_active ? 'Active' : 'Inactive'}</td></tr>)}{!employees.length && !error && <tr><td colSpan="3" className="empty">No employees found.</td></tr>}</tbody></table></div></div></div>;
}
