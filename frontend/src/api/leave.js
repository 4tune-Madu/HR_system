import { api } from './client';

export const saveLeavePolicy = (payload, id) => api(`${base()}/leave/policies/${id ? `${id}/` : ''}`, {method: id ? 'PATCH' : 'POST', body: JSON.stringify(payload)});
export const createPublicHoliday = payload => api(`${base()}/leave/holidays/`, {method: 'POST', body: JSON.stringify(payload)});
export const initializeLeaveBalances = year => api(`${base()}/leave/balances/`, {method: 'POST', body: JSON.stringify({year})});
export const saveWorkSchedule = (payload, id) => api(`${base()}/leave/work-schedules/${id ? `${id}/` : ''}`, {method: id ? 'PATCH' : 'POST', body: JSON.stringify(payload)});

const org = () => import.meta.env.VITE_ORGANIZATION_ID;
const base = () => `/leave/organizations/${org()}`;

export const listLeaveRequests = () => api(`${base()}/leave/requests/`);
export const listLeaveTypes = () => api(`${base()}/leave/types/`);
export const listLeavePolicies = () => api(`${base()}/leave/policies/`);
export const listLeaveBalances = () => api(`${base()}/leave/balances/`);
export const listPublicHolidays = () => api(`${base()}/leave/holidays/`);
export const listApprovalRules = () => api(`${base()}/leave/approval-rules/`);
export const listWorkSchedules = () => api(`${base()}/leave/work-schedules/`);
export const createLeaveRequest = (payload) => api(`${base()}/leave/requests/`, { method: 'POST', body: JSON.stringify(payload) });
export const submitLeaveRequest = (requestId) => api(`${base()}/leave/requests/${requestId}/submit/`, { method: 'POST' });
export const approveLeaveRequest = (requestId, review_comment = '') => api(`${base()}/leave/requests/${requestId}/approve/`, { method: 'POST', body: JSON.stringify({ review_comment }) });
export const rejectLeaveRequest = (requestId, review_comment = '') => api(`${base()}/leave/requests/${requestId}/reject/`, { method: 'POST', body: JSON.stringify({ review_comment }) });
export const cancelLeaveRequest = (requestId) => api(`${base()}/leave/requests/${requestId}/cancel/`, { method: 'POST' });
