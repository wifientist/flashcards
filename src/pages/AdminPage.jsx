import React, { useEffect, useState, useCallback } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

const ROLES = ['user', 'trusted', 'admin'];

export default function AdminPage() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [error, setError] = useState('');
  const [newUser, setNewUser] = useState({ email: '', password: '', roles: ['user'] });

  const loadUsers = useCallback(async () => {
    try {
      const data = await api.get('/api/auth/users');
      setUsers(data.users || []);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const loadSessions = useCallback(async () => {
    try {
      const data = await api.get('/api/admin/sessions');
      setSessions(data.sessions || []);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    loadUsers();
    loadSessions();
  }, [loadUsers, loadSessions]);

  const toggleRole = async (u, role) => {
    const has = (u.roles || []).includes(role);
    if (u.user_id === me?.user_id && role === 'admin' && has) {
      setError("You can't remove your own admin role.");
      return;
    }
    const roles = has ? u.roles.filter((r) => r !== role) : [...(u.roles || []), role];
    setError('');
    try {
      await api.put(`/api/auth/users/${u.user_id}/roles`, { roles });
      await loadUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const setActive = async (u, active) => {
    setError('');
    try {
      if (active) await api.post(`/api/auth/users/${u.user_id}/activate`);
      else await api.del(`/api/auth/users/${u.user_id}`);
      await loadUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleNewRole = (role) => {
    setNewUser((u) => ({
      ...u,
      roles: u.roles.includes(role) ? u.roles.filter((r) => r !== role) : [...u.roles, role],
    }));
  };

  const createUser = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/api/auth/users', {
        email: newUser.email,
        password: newUser.password,
        roles: newUser.roles.length ? newUser.roles : ['user'],
      });
      setNewUser({ email: '', password: '', roles: ['user'] });
      await loadUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const forceLogout = async (sessionId) => {
    setError('');
    try {
      await api.del(`/api/admin/sessions/${sessionId}`);
      await loadSessions();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
      {error && <div className="bg-red-100 text-red-800 text-sm p-2 rounded mb-4">{error}</div>}

      <form onSubmit={createUser} className="bg-white border rounded p-4 mb-6 space-y-3">
        <h2 className="font-semibold">Add a user</h2>
        <div className="flex flex-wrap gap-2">
          <input
            type="email"
            required
            placeholder="email"
            value={newUser.email}
            onChange={(e) => setNewUser((u) => ({ ...u, email: e.target.value }))}
            className="border p-2 rounded flex-1 min-w-[12rem]"
          />
          <input
            type="password"
            required
            placeholder="temporary password"
            value={newUser.password}
            onChange={(e) => setNewUser((u) => ({ ...u, password: e.target.value }))}
            className="border p-2 rounded flex-1 min-w-[12rem]"
          />
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-500">Roles:</span>
          {ROLES.map((role) => (
            <label key={role} className="flex items-center gap-1 cursor-pointer">
              <input type="checkbox" checked={newUser.roles.includes(role)} onChange={() => toggleNewRole(role)} />
              <span>{role}</span>
            </label>
          ))}
          <button type="submit" className="ml-auto bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            Create user
          </button>
        </div>
      </form>

      <h2 className="text-xl font-semibold mb-2">Users ({users.length})</h2>
      <div className="overflow-x-auto border rounded mb-8">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th className="p-2">Email</th>
              <th className="p-2">Roles</th>
              <th className="p-2">Last login</th>
              <th className="p-2">Status</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => {
              const isSelf = u.user_id === me?.user_id;
              return (
                <tr key={u.user_id} className="border-t">
                  <td className="p-2">
                    {u.email}{isSelf && <span className="text-xs text-gray-400"> (you)</span>}
                  </td>
                  <td className="p-2">
                    <div className="flex gap-3">
                      {ROLES.map((role) => (
                        <label key={role} className="flex items-center gap-1 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={(u.roles || []).includes(role)}
                            disabled={isSelf && role === 'admin'}
                            onChange={() => toggleRole(u, role)}
                          />
                          <span>{role}</span>
                        </label>
                      ))}
                    </div>
                  </td>
                  <td className="p-2 text-gray-500">
                    {u.last_login ? new Date(u.last_login).toLocaleDateString() : '—'}
                  </td>
                  <td className="p-2">
                    {u.is_active
                      ? <span className="text-green-700">Active</span>
                      : <span className="text-gray-400">Inactive</span>}
                  </td>
                  <td className="p-2">
                    {u.is_active ? (
                      <button
                        onClick={() => setActive(u, false)}
                        disabled={isSelf}
                        className="text-red-600 hover:underline disabled:text-gray-300 disabled:no-underline"
                      >
                        Deactivate
                      </button>
                    ) : (
                      <button onClick={() => setActive(u, true)} className="text-green-700 hover:underline">
                        Reactivate
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <h2 className="text-xl font-semibold mb-2">Active Sessions ({sessions.length})</h2>
      <div className="overflow-x-auto border rounded">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th className="p-2">Session</th>
              <th className="p-2">Roles</th>
              <th className="p-2">Created</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.session_id} className="border-t">
                <td className="p-2 font-mono text-xs">{s.session_id.slice(0, 8)}…</td>
                <td className="p-2">{(s.roles || []).join(', ')}</td>
                <td className="p-2 text-gray-500">
                  {s.created_at ? new Date(s.created_at).toLocaleString() : '—'}
                </td>
                <td className="p-2">
                  <button onClick={() => forceLogout(s.session_id)} className="text-red-600 hover:underline">
                    Force logout
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
