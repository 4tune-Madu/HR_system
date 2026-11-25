import React, {useCallback, useEffect, useRef, useState} from 'react';
import {Link, useParams} from 'react-router-dom';
import {ArrowLeft, Archive, FileText, RotateCcw, Upload} from 'lucide-react';
import {archiveDocument, downloadEmployeeDocument, getArchivedDocuments, getEmployee, getEmployeeDocument, listDocuments, listEmployees, restoreDocument, uploadDocument} from '../api/employees';
import {useAuth} from '../context/AuthContext';

const documentTypes = ['EMPLOYMENT_LETTER', 'OFFER_LETTER', 'CONTRACT', 'IDENTIFICATION', 'CERTIFICATE', 'RESUME', 'OTHER'];
const emptyForm = {document_type: 'OTHER', name: '', description: '', issue_date: '', expiry_date: '', file: null};

export default function Documents() {
	const {id} = useParams();
	const {user} = useAuth();
	const employeeId = id || user?.employee_id;
	const isOwnDocuments = !id;
	const [employee, setEmployee] = useState(null);
	const [employees, setEmployees] = useState([]);
	const [documents, setDocuments] = useState([]);
	const [view, setView] = useState('ACTIVE');
	const [form, setForm] = useState(emptyForm);
	const [selectedDocument, setSelectedDocument] = useState(null);
	const [error, setError] = useState('');
	const [message, setMessage] = useState('');
	const [busy, setBusy] = useState(false);
	const formRef = useRef(null);
	const membership = user?.memberships?.find((item) => item.organization_id === import.meta.env.VITE_ORGANIZATION_ID);
	const permissions = membership?.permissions || [];
	const has = (permission) => user?.is_system_admin || permissions.includes(permission);
	const canUpload = has('employee.document.upload');
	const canArchive = has('employee.document.archive');
	const canRestore = has('employee.document.restore');

	const loadData = useCallback(async () => {
		if (!employeeId) return;
		setError('');
		try {
			const [employeeData, documentData] = await Promise.all([
				isOwnDocuments ? Promise.resolve(null) : getEmployee(employeeId),
				view === 'ACTIVE' ? listDocuments(employeeId) : getArchivedDocuments(employeeId),
			]);
			setEmployee(employeeData);
			setDocuments(documentData);
		} catch (requestError) {
			setError(requestError.message);
		}
	}, [employeeId, isOwnDocuments, view]);

	useEffect(() => { loadData(); }, [loadData]);

	useEffect(() => {
		if (!employeeId) {
			listEmployees()
				.then(data => setEmployees(Array.isArray(data) ? data : data?.results || []))
				.catch(requestError => setError(requestError.message));
		}
	}, [employeeId]);

	const updateForm = (field, value) => setForm(current => ({...current, [field]: value}));

	const download = async record => {
		setError('');
		try {
			const blob = await downloadEmployeeDocument(employeeId, record.id);
			const url = URL.createObjectURL(blob);
			const link = document.createElement('a');
			link.href = url;
			link.download = decodeURIComponent(record.file.split('/').pop()) || record.name;
			link.click();
			setTimeout(() => URL.revokeObjectURL(url), 1000);
		} catch (requestError) { setError(requestError.message); }
	};

	const submitUpload = async event => {
		event.preventDefault();
		if (!form.file) {
			setError('Choose a file to upload.');
			return;
		}
		setBusy(true);
		setError('');
		setMessage('');
		try {
			const payload = new FormData();
			payload.append('document_type', form.document_type);
			payload.append('name', form.name);
			payload.append('description', form.description);
			if (form.issue_date) payload.append('issue_date', form.issue_date);
			if (form.expiry_date) payload.append('expiry_date', form.expiry_date);
			payload.append('file', form.file);
			await uploadDocument(employeeId, payload);
			setForm({...emptyForm});
			formRef.current?.reset();
			setMessage('Document uploaded.');
			if (view !== 'ACTIVE') setView('ACTIVE');
			else await loadData();
		} catch (requestError) {
			setError(requestError.message);
		} finally {
			setBusy(false);
		}
	};

	const archive = async document => {
		if (!window.confirm(`Archive “${document.name}”?`)) return;
		setBusy(true);
		setError('');
		setMessage('');
		try {
			await archiveDocument(employeeId, document.id);
			setSelectedDocument(null);
			setMessage('Document archived.');
			await loadData();
		} catch (requestError) {
			setError(requestError.message);
		} finally {
			setBusy(false);
		}
	};

	const restore = async document => {
		setBusy(true);
		setError('');
		setMessage('');
		try {
			await restoreDocument(employeeId, document.id);
			setSelectedDocument(null);
			setMessage('Document restored.');
			await loadData();
		} catch (requestError) {
			setError(requestError.message);
		} finally {
			setBusy(false);
		}
	};

	const showDetails = async document => {
		setError('');
		if (view === 'ARCHIVED') {
			setSelectedDocument(document);
			return;
		}
		try {
			setSelectedDocument(await getEmployeeDocument(employeeId, document.id));
		} catch (requestError) {
			setError(requestError.message);
		}
	};

	if (!employeeId) {
		return <div><div className="page-heading"><div><span className="eyebrow">Records</span><h2>Employee documents</h2><p>Choose an employee record to view and manage its documents.</p></div></div>{error && <div className="error banner" role="alert">{error}</div>}<section className="panel"><div className="table-wrap"><table><thead><tr><th>Employee</th><th>Employee number</th><th>Department</th><th>Action</th></tr></thead><tbody>{employees.length ? employees.map(item => <tr key={item.id}><td>{[item.identity?.first_name, item.identity?.last_name].filter(Boolean).join(' ') || 'Unnamed employee'}</td><td>{item.employee_number || '—'}</td><td>{item.assignment?.department_name || '—'}</td><td><Link className="link-button" to={`/employees/${item.id}/documents`}>View documents</Link></td></tr>) : <tr><td colSpan="4" className="empty">No employees available.</td></tr>}</tbody></table></div></section><Link className="back" to="/employees"><ArrowLeft size={17}/> Go to employees</Link></div>;
	}

	const employeeName = [employee?.identity?.first_name, employee?.identity?.last_name].filter(Boolean).join(' ') || [user?.first_name, user?.last_name].filter(Boolean).join(' ') || 'Employee';

	return <div>
		{!isOwnDocuments && <Link className="back" to={`/employees/${employeeId}`}><ArrowLeft size={17}/> {employeeName}</Link>}
		<div className="page-heading"><div><span className="eyebrow">{isOwnDocuments ? 'Employee self-service' : 'Employee records'}</span><h2>{isOwnDocuments ? 'My documents' : 'Documents'}</h2><p>{isOwnDocuments ? 'View and download documents shared with you by HR.' : `Upload, inspect, archive, and restore documents for ${employeeName}.`}</p></div></div>
		{error && <div className="error banner" role="alert">{error}</div>}
		{message && <div className="success banner" role="status">{message}</div>}
		{canUpload && <form ref={formRef} className="panel document-upload" onSubmit={submitUpload}>
			<h3><Upload size={18}/> Upload document</h3>
			<div className="form-grid">
				<label className="field">Document type<select value={form.document_type} onChange={event => updateForm('document_type', event.target.value)}>{documentTypes.map(type => <option key={type} value={type}>{type.replaceAll('_', ' ')}</option>)}</select></label>
				<label className="field">Name<input value={form.name} onChange={event => updateForm('name', event.target.value)} required maxLength={255}/></label>
				<label className="field">Issue date<input type="date" value={form.issue_date} onChange={event => updateForm('issue_date', event.target.value)}/></label>
				<label className="field">Expiry date<input type="date" value={form.expiry_date} onChange={event => updateForm('expiry_date', event.target.value)}/></label>
				<label className="field wide">Description<textarea value={form.description} onChange={event => updateForm('description', event.target.value)}/></label>
				<label className="field wide">File<input type="file" onChange={event => updateForm('file', event.target.files?.[0] || null)} required/></label>
			</div>
			<button className="primary" type="submit" disabled={busy}><Upload size={17}/>{busy ? 'Uploading…' : 'Upload document'}</button>
		</form>}
		<div className="toolbar document-toolbar">
			<div><h3>{view === 'ACTIVE' ? 'Active documents' : 'Archived documents'}</h3><p>{documents.length} records</p></div>
			<div className="segmented-control" role="group" aria-label="Document status">
				<button type="button" className={view === 'ACTIVE' ? 'selected' : ''} onClick={() => {setView('ACTIVE'); setSelectedDocument(null);}}>Active</button>
				<button type="button" className={view === 'ARCHIVED' ? 'selected' : ''} onClick={() => {setView('ARCHIVED'); setSelectedDocument(null);}}>Archived</button>
			</div>
		</div>
		<section className="panel"><div className="table-wrap"><table>
			<thead><tr><th>Name</th><th>Type</th><th>Issue date</th><th>Expiry date</th><th>Actions</th></tr></thead>
			<tbody>
				{documents.map(document => <tr key={document.id}>
					<td>{document.name}<small>{document.description || '—'}</small></td><td>{document.document_type?.replaceAll('_', ' ') || '—'}</td><td>{document.issue_date || '—'}</td><td>{document.expiry_date || '—'}</td>
					<td><div className="row-actions"><button className="link-button" type="button" onClick={() => showDetails(document)}>Details</button>{document.file && <button className="link-button" type="button" onClick={() => download(document)}>Download file</button>}{view === 'ACTIVE' && canArchive && <button className="link-button" type="button" disabled={busy} onClick={() => archive(document)}><Archive size={16}/> Archive</button>}{view === 'ARCHIVED' && canRestore && <button className="link-button" type="button" disabled={busy} onClick={() => restore(document)}><RotateCcw size={16}/> Restore</button>}</div></td>
				</tr>)}
				{!documents.length && <tr><td colSpan="5" className="empty">No {view.toLowerCase()} documents.</td></tr>}
			</tbody>
		</table></div></section>
		{selectedDocument && <section className="panel document-detail"><div className="panel-head"><div><h3>{selectedDocument.name}</h3><p>Document details</p></div><button className="link-button" type="button" onClick={() => setSelectedDocument(null)}>Close</button></div><div className="info-grid"><Info label="Type" value={selectedDocument.document_type}/><Info label="Description" value={selectedDocument.description}/><Info label="Issue date" value={selectedDocument.issue_date}/><Info label="Expiry date" value={selectedDocument.expiry_date}/><Info label="Created" value={selectedDocument.created_at}/><Info label="Updated" value={selectedDocument.updated_at}/></div></section>}
	</div>;
}

function Info({label, value}) {
	return <div className="info"><div><small>{label}</small></div><strong>{value || '—'}</strong></div>;
}
