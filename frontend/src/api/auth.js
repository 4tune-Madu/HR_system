import { api, clearTokens, saveTokens } from './client';
export async function login(email, password) { const data = await api('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) }, false); saveTokens(data); return data; }
export async function me() { return api('/auth/me/'); }
export async function logout() { const refresh = localStorage.getItem('refresh'); try { if (refresh) await api('/auth/logout/', { method: 'POST', body: JSON.stringify({ refresh }) }, false); } finally { clearTokens(); } }
