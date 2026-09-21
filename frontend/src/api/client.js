const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');

export function getAccessToken() { return localStorage.getItem('access'); }
export function getRefreshToken() { return localStorage.getItem('refresh'); }
export function saveTokens(data) { localStorage.setItem('access', data.access); localStorage.setItem('refresh', data.refresh); }
export function clearTokens() { localStorage.removeItem('access'); localStorage.removeItem('refresh'); }

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  const response = await fetch(`${API_URL}/auth/refresh/`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({refresh}) });
  if (!response.ok) return false;
  const data = await response.json();
  localStorage.setItem('access', data.access);
  return true;
}

export async function api(path, options = {}, retry = true) {
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const token = getAccessToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${API_URL}${path}`, {...options, headers});
  if (response.status === 401 && retry && await refreshAccessToken()) return api(path, options, false);
  const text = await response.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!response.ok) throw new Error(data?.detail || data?.message || (typeof data === 'string' ? data : 'Request failed'));
  return data;
}

export { API_URL };
