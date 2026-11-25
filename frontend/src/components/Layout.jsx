import React from 'react';
import {NavLink, Outlet, useNavigate} from 'react-router-dom';
import {LayoutDashboard, Users, Building2, FileText, Settings, LogOut, Menu, CalendarDays, Banknote, Clock3, UserRound} from 'lucide-react';
import {useAuth} from '../context/AuthContext';
import logo from '../../images/BTLogo.png';

export default function Layout(){
  const {user,logout}=useAuth();
  const nav=useNavigate();
  const [open,setOpen]=React.useState(false);
  const membership = user?.memberships?.find((item) => item.organization_id === import.meta.env.VITE_ORGANIZATION_ID);
  const permissions = membership?.permissions || [];
  const has = (permission) => user?.is_system_admin || permissions.includes(permission);
  const isEmployee = !user?.is_system_admin && !user?.is_hr_admin && !has('employee.view');

  const items = [
        ['/dashboard','Dashboard',LayoutDashboard],
        ...(has('employee.view') ? [['/employees','Employees',Users]] : []),
        ...(has('leave.view') ? [['/leave-management','Leave Management',CalendarDays]] : []),
        ...(has('payroll.view') || has('payroll.view_own') ? [['/payroll','Payroll',Banknote]] : []),
        ...(has('attendance.view') || isEmployee ? [['/attendance', isEmployee ? 'My Attendance' : 'Attendance', Clock3]] : []),
        ...(has('employee.document.view') ? [['/documents','Documents',FileText]] : []),
        ...(has('organization.structure.manage') ? [['/organization','Organization',Building2]] : []),
        ...(isEmployee ? [['/profile','My Profile',UserRound]] : [['/settings','Settings',Settings]]),
      ];

  return <div className="app-shell">
    <aside className={open?'sidebar open':'sidebar'}>
      <div className="brand">
        <img src={logo} alt="BT Technologies logo" />
        <div>
          <strong>BT Technologies</strong>
          <small>{user?.is_system_admin ? 'System administration' : 'People & Workforce'}</small>
        </div>
      </div>
      <nav>
        {items.map(([to,label,Icon,disabled])=>disabled
          ? <span key={label} className="nav-item nav-item-disabled" aria-disabled="true" title="Not available yet"><Icon size={19}/>{label}<small className="nav-status">Inactive</small></span>
          : <NavLink key={to} to={to} onClick={()=>setOpen(false)} className={({isActive})=>isActive?'nav-item active':'nav-item'}><Icon size={19}/>{label}</NavLink>)}
      </nav>
      <button className="logout" onClick={async()=>{await logout();nav('/login')}}><LogOut size={18}/>Logout</button>
    </aside>
    <main className="main">
      <header className="topbar">
        <button className="menu" onClick={()=>setOpen(!open)}><Menu/></button>
        <div>
          <h1>BT Technologies</h1>
          <p>{user?.is_system_admin ? 'Manage the platform, organization settings, and workforce.' : 'Manage your people, operations, and documents.'}</p>
        </div>
        <div className="user-chip">
          <div className="avatar">{user?.first_name?.[0]||user?.email?.[0]||'U'}</div>
          <span>{user?.first_name ? `${user.first_name} ${user.last_name}` : user?.email}</span>
        </div>
      </header>
      <section className="content"><Outlet/></section>
    </main>
  </div>
}
