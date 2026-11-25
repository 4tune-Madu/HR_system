import React, { useEffect, useMemo, useState } from 'react';
import { ArrowRight, Banknote, Building2, CalendarDays, Clock3, FileText, Plus, ShieldCheck, UserCheck, UserRound, Users, UserX, BriefcaseBusiness } from 'lucide-react';
import { Link } from 'react-router-dom';
import { listEmployees } from '../api/employees';
import { useAuth } from '../context/AuthContext';

const name = (employee) => [employee.identity?.first_name, employee.identity?.last_name].filter(Boolean).join(' ') || 'Unnamed employee';

export default function Dashboard() {
  const { user } = useAuth();
  const membership = user?.memberships?.find((item) => item.organization_id === import.meta.env.VITE_ORGANIZATION_ID);
  const permissions = membership?.permissions || [];
  const isSystemAdmin = user?.is_system_admin;
  const isHrAdmin = user?.is_hr_admin || permissions.includes('employee.view');
  if (!isSystemAdmin && !isHrAdmin) return <EmployeeDashboard user={user} />;
  return <AdminDashboard user={user} isSystemAdmin={isSystemAdmin} />;
}

function EmployeeDashboard({ user }) {
  const firstName = user?.first_name || user?.email?.split('@')[0] || 'there';
  return <div className="employee-dashboard">
    <div className="page-heading employee-welcome">
      <div>
        <span className="eyebrow">Employee self-service</span>
        <h2>Welcome back, {firstName}</h2>
        <p>Manage your leave, payslips, documents, and personal HR information from one place.</p>
      </div>
      <div className="employee-avatar"><UserRound size={24} /></div>
    </div>

    <div className="employee-quick-grid">
      <EmployeeQuickCard icon={CalendarDays} title="Request leave" text="Apply for annual, maternity, or sick leave and track approval." to="/leave-management" action="Open leave" />
      <EmployeeQuickCard icon={Banknote} title="My payslips" text="View released payroll entries and your net pay history." to="/payroll" action="View payslips" />
      <EmployeeQuickCard icon={FileText} title="My documents" text="Access employment documents shared with you by HR." to="/documents" action="View documents" />
      <EmployeeQuickCard icon={UserRound} title="My profile" text="Review your personal and employment account information." to="/profile" action="Open profile" />
    </div>

    <div className="employee-dashboard-grid">
      <section className="panel employee-next-step">
        <div className="panel-head"><div><h3>What you can do here</h3><p>Your employee portal puts the most useful HR actions within reach.</p></div></div>
        <div className="employee-checklist"><span><UserCheck size={17} /> Review your profile</span><span><CalendarDays size={17} /> Check leave availability</span><span><Banknote size={17} /> Download released payslips</span><span><FileText size={17} /> View HR documents</span></div>
      </section>
      <section className="panel employee-support-card">
        <ShieldCheck size={24} />
        <div><h3>Need help?</h3><p>Contact HR if a leave balance, payslip, or personal detail needs correction.</p></div>
      </section>
    </div>
  </div>;
}

function EmployeeQuickCard({ icon: Icon, title, text, to, action }) {
  return <Link className="employee-quick-card" to={to}><span className="employee-quick-icon"><Icon size={21} /></span><span><strong>{title}</strong><small>{text}</small><em>{action} <ArrowRight size={15} /></em></span></Link>;
}

function AdminDashboard({ user, isSystemAdmin }) {
  const [employees, setEmployees] = useState([]);
  const [error, setError] = useState('');
  useEffect(() => { listEmployees().then(setEmployees).catch((requestError) => setError(requestError.message)); }, []);
  const active = employees.filter((employee) => employee.is_active).length;
  const inactive = employees.length - active;
  const probation = employees.filter((employee) => employee.employment?.employment_status === 'PROBATION').length;
  const recent = useMemo(() => employees.slice(0, 6), [employees]);
  if (isSystemAdmin) return <SystemAdminDashboard employees={employees} active={active} inactive={inactive} recent={recent} error={error} />;
  return <HrAdminDashboard employees={employees} active={active} inactive={inactive} probation={probation} recent={recent} error={error} isHrAdmin={user?.is_hr_admin} />;
}

function HrAdminDashboard({ employees, active, inactive, probation, recent, error, isHrAdmin }) {
  return <div><div className="page-heading"><div><span className="eyebrow">Workforce overview</span><h2>HR Admin Dashboard</h2><p>Monitor your workforce, employee records, and people operations.</p></div><Link className="primary" to="/employees/new"><Plus size={18} /> Add employee</Link></div>{error && <div className="error banner">{error}</div>}<div className="stats"><Stat icon={Users} label="Total employees" value={employees.length} /><Stat icon={UserCheck} label="Active employees" value={active} /><Stat icon={BriefcaseBusiness} label="On probation" value={probation} /><Stat icon={UserX} label="Inactive" value={inactive} /></div>{!isHrAdmin && <div className="panel" style={{ marginBottom: 16 }}><div className="panel-head"><div><h3>Access level</h3><p>Your account is not assigned to an HR admin role.</p></div></div></div>}<div className="panel"><div className="panel-head"><div><h3>Recent employees</h3><p>Your latest employee records.</p></div><Link to="/employees">View all <ArrowRight size={16} /></Link></div><EmployeeRows employees={recent} /></div></div>;
}

function SystemAdminDashboard({ employees, active, inactive, recent, error }) {
  return <div>
    <div className="page-heading">
      <div><span className="eyebrow">Administration</span><h2>System Admin Dashboard</h2><p>Manage platform settings, workforce health, and operational controls.</p></div>
      <div className="table-actions"><Link className="primary" to="/employees/new"><Plus size={18} /> Add employee</Link><Link className="link-button" to="/organization"><Building2 size={18} /> Organization</Link></div>
    </div>
    {error && <div className="error banner">{error}</div>}
    <div className="stats"><Stat icon={ShieldCheck} label="Platform access" value="Full" /><Stat icon={Users} label="Total employees" value={employees.length} /><Stat icon={UserCheck} label="Active employees" value={active} /><Stat icon={UserX} label="Inactive" value={inactive} /></div>

    <section className="panel admin-console-panel">
      <div className="panel-head"><div><h3>Admin workspace</h3><p>Use the focused workspace for each operational task.</p></div></div>
      <div className="admin-action-grid">
        <AdminAction icon={Users} title="Employee records" text="Create, update, and review workforce details." to="/employees" action="Open employees" />
        <AdminAction icon={Building2} title="Organization structure" text="Maintain branches, departments, units, grades, and positions." to="/organization" action="Manage structure" />
        <AdminAction icon={Clock3} title="Attendance operations" text="Review attendance, device status, and employee mappings." to="/attendance" action="Open attendance" />
        <AdminAction icon={CalendarDays} title="Leave management" text="Review requests, balances, holidays, and approvals." to="/leave-management" action="Open leave" />
        <AdminAction icon={Banknote} title="Payroll" text="Manage payroll runs and employee pay records." to="/payroll" action="Open payroll" />
        <AdminAction icon={FileText} title="Documents" text="Manage employee documents and access." to="/documents" action="Open documents" />
      </div>
    </section>

    <section className="panel admin-overview-panel">
      <div className="panel-head"><div><h3>System overview</h3><p>Keep employee records and organization controls current.</p></div></div>
      <div className="notice"><ShieldCheck size={18} /><div><h3>System administrator access</h3><p>You have full access to organization administration. Attendance device registration and mapping are handled from the dedicated Attendance page.</p></div></div>
    </section>

    <section className="panel recent-employees-panel">
      <div className="panel-head"><div><h3>Recent employees</h3><p>Latest employee records across the platform.</p></div><Link to="/employees">View all <ArrowRight size={16} /></Link></div>
      <EmployeeRows employees={recent} />
    </section>
  </div>;
}

function AdminAction({ icon: Icon, title, text, to, action }) {
  return <Link className="admin-action-card" to={to}><span className="admin-action-icon"><Icon size={20} /></span><span><strong>{title}</strong><small>{text}</small><em>{action} <ArrowRight size={15} /></em></span></Link>;
}

function Stat({ icon: Icon, label, value }) { return <div className="stat"><div className="stat-icon"><Icon size={21} /></div><div><small>{label}</small><strong>{value}</strong></div></div>; }
function EmployeeRows({ employees }) { return <div className="table-wrap"><table><thead><tr><th>Employee</th><th>Employee ID</th><th>Department</th><th>Position</th><th>Status</th></tr></thead><tbody>{employees.map((employee) => <tr key={employee.id}><td><Link className="employee-name" to={`/employees/${employee.id}`}>{name(employee)}</Link><small>{employee.contact?.company_email || employee.contact?.personal_email || '—'}</small></td><td>{employee.employee_number || '—'}</td><td>{employee.assignment?.department_name || '—'}</td><td>{employee.assignment?.position_name || '—'}</td><td><span className={employee.is_active ? 'status active' : 'status inactive'}>{employee.is_active ? 'Active' : 'Inactive'}</span></td></tr>)}{!employees.length && <tr><td colSpan="5" className="empty">No employees found.</td></tr>}</tbody></table></div>; }
