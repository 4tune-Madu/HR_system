import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute, { PermissionRoute } from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Employees from './pages/Employees';
import EmployeeDetails from './pages/EmployeeDetails';
import EmployeeForm from './pages/EmployeeForm';
import Organization from './pages/Organization';
import Documents from './pages/Documents';
import Settings from './pages/Settings';
import LeaveManagement from './pages/LeaveManagement';
import Attendance from './pages/Attendance';
import Payroll from './pages/Payroll';
import MyProfile from './pages/MyProfile';
import Onboarding from './pages/Onboarding';
import './styles.css';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/profile" element={<MyProfile />} />

              <Route element={<PermissionRoute permission="employee.view" />}>
                <Route path="/employees" element={<Employees />} />
                <Route path="/employees/:id" element={<EmployeeDetails />} />
                <Route path="/onboarding" element={<Onboarding />} />
              </Route>

              <Route element={<PermissionRoute permission="employee.document.view" />}>
                <Route path="/employees/:id/documents" element={<Documents />} />
              </Route>

              <Route element={<PermissionRoute permission="employee.create" />}>
                <Route path="/employees/new" element={<EmployeeForm />} />
              </Route>

              <Route element={<PermissionRoute permission="employee.update" />}>
                <Route path="/employees/:id/edit" element={<EmployeeForm />} />
              </Route>

              <Route element={<PermissionRoute permission="leave.view" />}>
                <Route path="/leave-management" element={<LeaveManagement />} />
              </Route>

              <Route element={<PermissionRoute permission="attendance.view" />}>
                <Route path="/attendance" element={<Attendance />} />
              </Route>

              <Route element={<PermissionRoute permission="payroll.view" />}>
                <Route path="/payroll" element={<Payroll />} />
              </Route>

              <Route element={<PermissionRoute permission="organization.structure.manage" />}>
                <Route path="/organization" element={<Organization />} />
              </Route>

              <Route element={<PermissionRoute permission="employee.document.view" />}>
                <Route path="/documents" element={<Documents />} />
              </Route>

              <Route path="/settings" element={<Settings />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
