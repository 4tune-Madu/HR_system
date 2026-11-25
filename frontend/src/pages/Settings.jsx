import React, {useEffect, useState} from 'react';
import {ShieldCheck, UserRound, Globe2, KeyRound} from 'lucide-react';
import {me} from '../api/auth';

const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');
const ORGANIZATION_ID = import.meta.env.VITE_ORGANIZATION_ID || 'Not configured';

export default function Settings() {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    me()
      .then((user) => setProfile(user))
      .catch((requestError) => setError(requestError.message));
  }, []);

  const userName = profile ? `${profile.first_name || ''} ${profile.last_name || ''}`.trim() || profile.email : 'Unknown user';

  return (
    <div>
      <div className="page-heading">
        <div>
          <span className="eyebrow">Account</span>
          <h2>Settings</h2>
          <p>Review the active account and current application configuration.</p>
        </div>
      </div>

      {error && <div className="error banner">{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '18px' }}>
        <section className="panel">
          <div className="panel-head">
            <div>
              <h3><UserRound size={18} /> Profile</h3>
            </div>
          </div>
          {profile ? (
            <div style={{ display: 'grid', gap: '12px' }}>
              <Info label="Full name" value={userName} />
              <Info label="Email" value={profile.email} />
              <Info label="Account active" value={profile.is_active ? 'Yes' : 'No'} />
              <Info label="Staff access" value={profile.is_staff ? 'Yes' : 'No'} />
            </div>
          ) : (
            <p className="empty">Loading account details…</p>
          )}
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <h3><ShieldCheck size={18} /> Security</h3>
            </div>
          </div>
          <div style={{ display: 'grid', gap: '12px' }}>
            <Info label="Authentication status" value={localStorage.getItem('access') ? 'Authenticated' : 'Not authenticated'} />
            <Info label="Token refresh available" value={localStorage.getItem('refresh') ? 'Yes' : 'No'} />
            <Info label="Password setup" value="Managed through the invitation flow" />
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <h3><Globe2 size={18} /> Environment</h3>
            </div>
          </div>
          <div style={{ display: 'grid', gap: '12px' }}>
            <Info label="API URL" value={API_URL} />
            <Info label="Organization ID" value={ORGANIZATION_ID} />
            <Info label="Session" value={localStorage.getItem('access') ? 'Live session' : 'No active session'} />
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <h3><KeyRound size={18} /> Access summary</h3>
            </div>
          </div>
          <div style={{ display: 'grid', gap: '12px' }}>
            <Info label="Current module" value="HR System" />
            <Info label="Access scope" value="Organization-scoped" />
            <Info label="Frontend config" value="Set in the Vite environment variables" />
          </div>
        </section>
      </div>
    </div>
  );
}

function Info({ label, value }) {
  return (
    <div className="info">
      <div><small>{label}</small></div>
      <strong>{value || '—'}</strong>
    </div>
  );
}
