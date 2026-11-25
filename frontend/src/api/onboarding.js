import { api } from './client';

const base = () => {
  const organizationId = import.meta.env.VITE_ORGANIZATION_ID;
  if (!organizationId) throw new Error('VITE_ORGANIZATION_ID is not configured.');
  return `/onboarding/organizations/${organizationId}/onboarding/tasks`;
};

export const listOnboardingTasks = () => api(`${base()}/`);
export const createOnboardingTask = (payload) => api(`${base()}/`, { method: 'POST', body: JSON.stringify(payload) });
export const updateOnboardingTask = (taskId, payload) => api(`${base()}/${taskId}/`, { method: 'PATCH', body: JSON.stringify(payload) });
