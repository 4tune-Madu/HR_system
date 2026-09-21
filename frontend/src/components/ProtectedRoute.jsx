import React from 'react'; import {Navigate,Outlet} from 'react-router-dom'; import {useAuth} from '../context/AuthContext';
export default function ProtectedRoute(){const {user,loading}=useAuth(); if(loading)return <div className="loading-screen">Loading HR System…</div>; return user?<Outlet/>:<Navigate to="/login" replace/>;}
