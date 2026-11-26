import React, { useEffect, useState } from 'react';
import { getAttendanceSettings, updateAttendanceSettings } from '../api/organization';

export default function Organization() {
	const [enabled, setEnabled] = useState(false);
	const [loading, setLoading] = useState(true);
	const [saving, setSaving] = useState(false);
	const [error, setError] = useState('');
	const [notice, setNotice] = useState('');

	useEffect(() => {
		getAttendanceSettings()
			.then((settings) => setEnabled(Boolean(settings.automatic_attendance_checkout_enabled)))
			.catch((err) => setError(err.message))
			.finally(() => setLoading(false));
	}, []);

	const save = async (event) => {
		event.preventDefault();
		setSaving(true);
		setError('');
		setNotice('');
		try {
			const settings = await updateAttendanceSettings({ automatic_attendance_checkout_enabled: enabled });
			setEnabled(Boolean(settings.automatic_attendance_checkout_enabled));
			setNotice('Attendance settings saved.');
		} catch (err) {
			setError(err.message);
		} finally {
			setSaving(false);
		}
	};

	return (
		<div>
			<div className="page-heading">
				<div><span className="eyebrow">Structure</span><h2>Organization</h2><p>Organization-level workforce and attendance settings.</p></div>
			</div>
			{error && <div className="error banner">{error}</div>}
			{notice && <div className="notice banner">{notice}</div>}
			<form className="panel" onSubmit={save}>
				<div className="panel-head">
					<div><h3>Attendance settings</h3><p>Control automatic checkout for this organization.</p></div>
				</div>
				<label className="field checkbox-field">
					<input
						type="checkbox"
						checked={enabled}
						disabled={loading || saving}
						onChange={(event) => setEnabled(event.target.checked)}
					/>
					<span>Enable automatic attendance checkout</span>
				</label>
				<button className="primary" type="submit" disabled={loading || saving}>
					{saving ? 'Saving…' : 'Save settings'}
				</button>
			</form>
			<div className="panel notice">
				<p>Branch, department, team, position, and job-grade management endpoints are not currently exposed by the backend.</p>
			</div>
		</div>
	);
}
