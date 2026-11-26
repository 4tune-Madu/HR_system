import { api } from './client';

const base = () => `/leave/organizations/${import.meta.env.VITE_ORGANIZATION_ID}/leave`;

export const listLeaveRequests = () => api(`${base()}/requests/`);
export const listLeaveTypes = () => api(`${base()}/types/`);
