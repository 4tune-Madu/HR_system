import { api } from './client';

const base = () => {
	const organizationId = import.meta.env.VITE_ORGANIZATION_ID;
	if (!organizationId) throw new Error('VITE_ORGANIZATION_ID is not configured.');
	return `/employees/organizations/${organizationId}/employees`;
};

export const listEmployees = () => api(`${base()}/`);
export const getEmployee = employeeId => api(`${base()}/${employeeId}/`);
export const createEmployee = payload => api(`${base()}/`, {method: 'POST', body: JSON.stringify(payload)});
export const updateEmployee = (employeeId, payload) => api(`${base()}/${employeeId}/`, {method: 'PATCH', body: JSON.stringify(payload)});
export const deactivateEmployee = employeeId => api(`${base()}/${employeeId}/`, {method: 'POST'});
export const activateEmployee = employeeId => api(`${base()}/${employeeId}/activate/`, {method: 'POST'});
export const listDocuments = employeeId => api(`${base()}/${employeeId}/documents/`);
export const getArchivedDocuments = employeeId => api(`${base()}/${employeeId}/documents/archived/`);
export const getEmployeeDocument = (employeeId, documentId) => api(`${base()}/${employeeId}/documents/${documentId}/`);
export const downloadEmployeeDocument = (employeeId, documentId) => api(`${base()}/${employeeId}/documents/${documentId}/download/`, {responseType: 'blob'});
export const uploadDocument = (employeeId, formData) => api(`${base()}/${employeeId}/documents/`, {method: 'POST', body: formData});
export const archiveDocument = (employeeId, documentId) => api(`${base()}/${employeeId}/documents/${documentId}/`, {method: 'DELETE'});
export const restoreDocument = (employeeId, documentId) => api(`${base()}/${employeeId}/documents/${documentId}/restore/`, {method: 'POST'});
export const provisionEmployeeAccount = employeeId => api(`${base()}/${employeeId}/account/provision/`, {method: 'POST', body: JSON.stringify({})});
export const inviteEmployeeAccount = employeeId => api(`${base()}/${employeeId}/account/invite/`, {method: 'POST'});
