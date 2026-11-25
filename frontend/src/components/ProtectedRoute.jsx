import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute() {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-screen">Loading BT Technologies…</div>;
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}

export function PermissionRoute({ permission }) {
  const { user } = useAuth();
  const membership = user?.memberships?.find((item) => item.organization_id === import.meta.env.VITE_ORGANIZATION_ID);
  const alternatives = permission === 'payroll.view' ? ['payroll.view_own'] : permission === 'attendance.view' ? ['attendance.view_own', 'employee.view_own'] : [];
  const allowed = user?.is_system_admin || membership?.permissions?.includes(permission) || alternatives.some((item) => membership?.permissions?.includes(item));
  return allowed ? <Outlet /> : <Navigate to="/dashboard" replace />;
}
