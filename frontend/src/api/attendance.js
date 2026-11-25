import { api } from './client';

const base = () => {
  const organizationId = import.meta.env.VITE_ORGANIZATION_ID;
  if (!organizationId) throw new Error('VITE_ORGANIZATION_ID is not configured.');
  return `/attendance/organizations/${organizationId}/attendance`;
};

const devicesBase = () => {
  const organizationId = import.meta.env.VITE_ORGANIZATION_ID;
  if (!organizationId) throw new Error('VITE_ORGANIZATION_ID is not configured.');
  return `/attendance/organizations/${organizationId}/attendance/devices`;
};

export const listAttendanceRecords = () => api(`${base()}/records/`);
export const listAttendanceSyncLogs = (deviceId) => api(`${base()}/sync-logs/${deviceId ? `?device_id=${deviceId}` : ''}`);
export const listAttendanceDevices = () => api(`${devicesBase()}/`);
export const createAttendanceDevice = (payload) => api(`${devicesBase()}/`, { method: 'POST', body: JSON.stringify(payload) });
export const updateAttendanceDevice = (deviceId, payload) => api(`${devicesBase()}/${deviceId}/`, { method: 'PATCH', body: JSON.stringify(payload) });
export const getDeviceUsers = (deviceId) => api(`${devicesBase()}/${deviceId}/users/`);
export const getDeviceMappings = (deviceId) => api(`${devicesBase()}/${deviceId}/mappings/`);
export const createDeviceMapping = (deviceId, payload) => api(`${devicesBase()}/${deviceId}/mappings/`, {
  method: 'POST',
  body: JSON.stringify(payload),
});
export const updateDeviceMapping = (deviceId, deviceUserId, payload) => api(`${devicesBase()}/${deviceId}/mappings/${deviceUserId}/`, {
  method: 'PATCH',
  body: JSON.stringify(payload),
});
export const deleteDeviceMapping = (deviceId, deviceUserId) => api(`${devicesBase()}/${deviceId}/mappings/${deviceUserId}/`, {
  method: 'DELETE',
});
export const manualCheckIn = (payload) => api(`${base()}/manual/check-in/`, {
  method: 'POST',
  body: JSON.stringify(payload),
});
export const syncDevice = (deviceId, payload = {}) => api(`${devicesBase()}/${deviceId}/sync/`, {
  method: 'POST',
  body: JSON.stringify(payload),
});
export const reconcileAttendanceRecord = (recordId) => api(`${base()}/records/${recordId}/reconcile/`, { method: 'POST' });
