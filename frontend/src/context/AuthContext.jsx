import React, {createContext, useContext, useEffect, useState} from 'react';
import {login as loginApi, logout as logoutApi, me} from '../api/auth';
import {getAccessToken} from '../api/client';
const AuthContext = createContext(null);
export function AuthProvider({children}) {
  const [user,setUser]=useState(null); const [loading,setLoading]=useState(true);
  useEffect(()=>{ if(!getAccessToken()){setLoading(false);return;} me().then(setUser).catch(()=>setUser(null)).finally(()=>setLoading(false)); },[]);
  const login=async(email,password)=>{await loginApi(email,password); setUser(await me());};
  const logout=async()=>{await logoutApi();setUser(null);};
  return <AuthContext.Provider value={{user,loading,login,logout}}>{children}</AuthContext.Provider>;
}
export const useAuth=()=>useContext(AuthContext);
