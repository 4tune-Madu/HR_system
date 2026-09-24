import React, {useEffect, useState} from 'react';
import {Link, useParams} from 'react-router-dom';
import {getEmployee} from '../api/employees';

export default function EmployeeDetails() {
  const {id} = useParams(); const [employee, setEmployee] = useState(null); const [error, setError] = useState('');
  useEffect(() => { getEmployee(id).then(setEmployee).catch(error => setError(error.message)); }, [id]);
  if (error) return <div className="error banner">{error}</div>;
  if (!employee) return <div className="loading">Loading employee...</div>;
  const name = [employee.identity?.first_name, employee.identity?.last_name].filter(Boolean).join(' ') || 'Unnamed employee';
  return <div><Link className="back" to="/employees">Back to employees</Link><div className="page-heading"><div><span className="eyebrow">Employee profile</span><h2>{name}</h2><p>{employee.assignment?.position_name || 'Position not assigned'}</p></div><Link className="secondary" to={`/employees/${id}/edit`}>Edit</Link></div><div className="panel"><p>Email: {employee.contact?.company_email || employee.contact?.personal_email || '—'}</p><p>Status: {employee.is_active ? 'Active' : 'Inactive'}</p></div></div>;
}
