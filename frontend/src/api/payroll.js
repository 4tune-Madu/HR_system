import { api, listAll } from './client';

export const listSalaryStructures = () => listAll(`${base()}/structures/`);
export const saveSalaryStructure = (payload, id) => api(`${base()}/structures/${id ? `${id}/` : ''}`, {method: id ? 'PATCH' : 'POST', body: JSON.stringify(payload)});

const base = () => {
  const organizationId = import.meta.env.VITE_ORGANIZATION_ID;
  if (!organizationId) throw new Error('VITE_ORGANIZATION_ID is not configured.');
  return `/payroll/organizations/${organizationId}/payroll`;
};

export const listPayrollPeriods = () => api(`${base()}/periods/`);
export const createPayrollPeriod = (payload) => api(`${base()}/periods/`, { method: 'POST', body: JSON.stringify(payload) });
export const processPayrollPeriod = (periodId) => api(`${base()}/periods/${periodId}/process/`, { method: 'POST' });
export const listPayrollRuns = () => api(`${base()}/runs/`);
export const getPayrollRun = (runId) => api(`${base()}/runs/${runId}/`);
export const listMyPayrollEntries = () => api(`${base()}/my-entries/`);
export const approvePayrollRun = (runId) => api(`${base()}/runs/${runId}/approve/`, { method: 'POST' });
export const markPayrollRunPaid = (runId) => api(`${base()}/runs/${runId}/mark-paid/`, { method: 'POST' });
export const listCompensation = () => api(`${base()}/compensation/`);
export const createCompensation = (payload) => api(`${base()}/compensation/`, { method: 'POST', body: JSON.stringify(payload) });
export const listPayrollComponents = () => api(`${base()}/components/`);
export const createPayrollComponent = (payload) => api(`${base()}/components/`, { method: 'POST', body: JSON.stringify(payload) });
