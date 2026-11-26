import { api } from './client';

const settingsUrl = () => `/organization/${import.meta.env.VITE_ORGANIZATION_ID}/attendance/settings/`;

export const getAttendanceSettings = () => api(settingsUrl());
export const updateAttendanceSettings = (payload) => api(settingsUrl(), {
  method: 'PATCH',
  body: JSON.stringify(payload),
});
