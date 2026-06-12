import React, { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function AdminPage() {
  const [sessions, setSessions] = useState([]);
  const [users, setUsers] = useState([]);
  const [roleEdits, setRoleEdits] = useState({}); // user_id -> comma string
  const [error, setError] = useState('');

  const loadUsers = async () => {
    try {
      const data = await api.get('/api/auth/users');
      setUsers(data.users || []);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadUsers();
    api
      .get('/api/admin/sessions')
      .then((data) => setSessions(data.sessions || []))
      .catch((err) => setError(err.message));
  }, []);

  const handleRoleChange = (userId, roles) => {
    setRoleEdits((prev) => ({ ...prev, [userId]: roles }));
  };

  const updateRoles = async (userId) => {
    const draft = roleEdits[userId];
    if (draft == null) return;
    const roles = draft.split(',').map((r) => r.trim()).filter(Boolean);
    try {
      // Correct endpoint: roles live on the user, not the session, and are
      // wrapped in a { roles: [...] } body (RoleUpdateRequest).
      await api.put(`/api/auth/users/${userId}/roles`, { roles });
      setRoleEdits((prev) => {
        const next = { ...prev };
        delete next[userId];
        return next;
      });
      await loadUsers();
    } catch (err) {
      alert(`Failed to update roles: ${err.message}`);
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl mb-4">Admin Dashboard</h1>
      {error && (
        <div className="bg-red-100 text-red-800 text-sm p-2 rounded mb-4">{error}</div>
      )}

      <h2 className="text-xl mb-4">Users</h2>
      {users.map((user) => (
        <div key={user.user_id} className="border p-4 mb-2">
          <p><strong>User:</strong> {user.email}</p>
          <p><strong>Roles:</strong> {(user.roles || []).join(', ')}</p>
          <div className="mt-2 flex items-center">
            <input
              type="text"
              placeholder="Comma-separated roles, e.g. user,admin"
              className="border p-1 mr-2 flex-1"
              value={roleEdits[user.user_id] ?? (user.roles || []).join(', ')}
              onChange={(e) => handleRoleChange(user.user_id, e.target.value)}
            />
            <button
              className="px-2 py-1 border bg-gray-100"
              onClick={() => updateRoles(user.user_id)}
            >
              Update Roles
            </button>
          </div>
        </div>
      ))}

      <h2 className="text-xl mb-4 mt-6">Active Sessions</h2>
      {sessions.map((session) => (
        <div key={session.session_id} className="border p-4 mb-2">
          <p><strong>Session:</strong> {session.session_id}</p>
          <p><strong>Authenticated:</strong> {String(session.authenticated)}</p>
          <p><strong>Roles:</strong> {(session.roles || []).join(', ')}</p>
        </div>
      ))}
    </div>
  );
}
