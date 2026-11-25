const API_URL = (import.meta.env?.VITE_API_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');

export function getAccessToken() { return localStorage.getItem('access'); }
export function getRefreshToken() { return localStorage.getItem('refresh'); }
export function saveTokens(data) { localStorage.setItem('access', data.access); localStorage.setItem('refresh', data.refresh); }
export function clearTokens() { localStorage.removeItem('access'); localStorage.removeItem('refresh'); }

let pendingRefresh = null;

async function performRefresh() {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  const response = await fetch(`${API_URL}/auth/refresh/`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({refresh}) });
  if (!response.ok) return false;
  const data = await response.json();
  localStorage.setItem('access', data.access);
  if (data.refresh) localStorage.setItem('refresh', data.refresh);
  return true;
}

function refreshAccessToken() {
  if (!pendingRefresh) {
    pendingRefresh = performRefresh().finally(() => { pendingRefresh = null; });
  }
  return pendingRefresh;
}

function errorMessage(data, prefix = '') {
  if (typeof data === 'string') return prefix ? `${prefix}: ${data}` : data;
  if (Array.isArray(data)) return data.map((item) => errorMessage(item, prefix)).filter(Boolean).join(' ');
  if (data && typeof data === 'object') {
    return Object.entries(data).map(([key, value]) => errorMessage(value,
      ['detail', 'message', 'non_field_errors'].includes(key) ? prefix : [prefix, key.replaceAll('_', ' ')].filter(Boolean).join(' — ')
    )).filter(Boolean).join(' ');
  }
  return '';
}

export async function api(path, options = {}, retry = true) {
  const { responseType, ...requestOptions } = options;
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const token = getAccessToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  let response;
  try { response = await fetch(`${API_URL}${path}`, {...requestOptions, headers}); }
  catch { throw new Error('Cannot connect to the HR API. Check that the local backend is running.'); }
  if (response.status === 401 && retry) {
    if (await refreshAccessToken()) return api(path, options, false);
    clearTokens();
  }
  if (response.ok && responseType === 'blob') return response.blob();
  const text = await response.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!response.ok) throw new Error(errorMessage(data) || 'Request failed');
  return data;
}

export { API_URL };

export async function listAll(path) {
  const results = [];
  let next = path;
  while (next) {
    const data = await api(next);
    if (Array.isArray(data)) return results.concat(data);
    results.push(...(data?.results || []));
    if (!data?.next) break;
    const url = new URL(data.next, `${API_URL}/`);
    const base = new URL(`${API_URL}/`);
    if (url.origin !== base.origin || !url.pathname.startsWith(base.pathname)) {
      throw new Error('The API returned an invalid pagination URL.');
    }
    next = `/${url.pathname.slice(base.pathname.length)}${url.search}`;
  }
  return results;
}
