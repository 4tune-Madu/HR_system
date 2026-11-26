import { api } from './client';

const base = () => `/attendance/organizations/${import.meta.env.VITE_ORGANIZATION_ID}/attendance`;

export const listAttendanceRecords = () => api(`${base()}/records/`);
