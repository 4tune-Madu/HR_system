import { api } from './client';

const org = () => import.meta.env.VITE_ORGANIZATION_ID;
const base = () => `/employees/organizations/${org()}/employees`;
export const listEmployees = () => api(`${base()}/`);
export const getEmployee = id => api(`${base()}/${id}/`);
export const createEmployee = payload => api(`${base()}/`, {method: 'POST', body: JSON.stringify(payload)});
export const updateEmployee = (id, payload) => api(`${base()}/${id}/`, {method: 'PATCH', body: JSON.stringify(payload)});
export const deactivateEmployee = id => api(`${base()}/${id}/`, {method: 'POST'});
export const listDocuments = id => api(`${base()}/${id}/documents/`);
