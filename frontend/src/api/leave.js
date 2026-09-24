import { api } from './client';

const org = () => import.meta.env.VITE_ORGANIZATION_ID;
const base = () => `/leave/organizations/${org()}`;

export const listLeaveRequests = () => api(`${base()}/leave/requests/`);
export const listLeaveTypes = () => api(`${base()}/leave/types/`);
