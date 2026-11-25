import { api, listAll } from './client';

const base = () => {
  const organizationId = import.meta.env.VITE_ORGANIZATION_ID;
  if (!organizationId) throw new Error('VITE_ORGANIZATION_ID is not configured.');
  return `/organization/${organizationId}`;
};

export const getAttendanceSettings = () => api(`${base()}/attendance/settings/`);
export const updateAttendanceSettings = (payload) => api(`${base()}/attendance/settings/`, {
  method: 'PATCH',
  body: JSON.stringify(payload),
});

export const listBranches = () => listAll(`${base()}/branches/`);
export const listDepartments = () => listAll(`${base()}/departments/`);
export const listTeams = () => listAll(`${base()}/teams/`);
export const listJobGrades = () => listAll(`${base()}/job-grades/`);
export const listPositions = () => listAll(`${base()}/positions/`);

const resource = (name) => `${base()}/${name}/`;
export const createStructureItem = (name, payload) => api(resource(name), { method: 'POST', body: JSON.stringify(payload) });
export const updateStructureItem = (name, id, payload) => api(`${resource(name)}${id}/`, { method: 'PATCH', body: JSON.stringify(payload) });
export const deleteStructureItem = (name, id) => api(`${resource(name)}${id}/`, { method: 'DELETE' });
