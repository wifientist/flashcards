import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import DashboardPage from './DashboardPage';
import ProposalsPage from './ProposalsPage';

const TABS = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'proposals', label: 'My Proposals' },
];

// The user's home base: account info plus their progress dashboard and the
// edits they've proposed. Active tab is kept in the URL (?tab=proposals).
export default function ProfilePage() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const tabParam = params.get('tab');
  const active = TABS.some((t) => t.key === tabParam) ? tabParam : 'dashboard';

  const setTab = (key) => setParams(key === 'dashboard' ? {} : { tab: key }, { replace: true });

  return (
    <div>
      <div className="max-w-2xl mx-auto px-4 pt-4">
        <h1 className="text-2xl font-bold">Profile</h1>
        {user && (
          <p className="text-sm text-gray-500 mt-1">
            {user.email} · {(user.roles || ['user']).join(', ')}
          </p>
        )}
        <div className="flex gap-2 mt-3">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-1.5 rounded text-sm transition ${
                active === t.key ? 'bg-blue-600 text-white' : 'bg-white border hover:bg-gray-100'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {active === 'dashboard' && <DashboardPage />}
      {active === 'proposals' && <ProposalsPage />}
    </div>
  );
}
