import React, { useEffect, useState } from 'react';

export default function AdminPage() {
  const [sessions, setSessions] = useState([]);
  const [newRoles, setNewRoles] = useState({});

  useEffect(() => {
    fetch('/api/admin/sessions', { credentials: 'include' })
      .then(res => res.json())
      .then(data => setSessions(data.sessions));
  }, []);

  const handleRoleChange = (sessionId, roles) => {
    setNewRoles(prev => ({ ...prev, [sessionId]: roles }));
  };

  const updateRoles = async (sessionId) => {
    const roles = newRoles[sessionId].split(',').map(r => r.trim());

    const res = await fetch(`/api/admin/sessions/${sessionId}/roles`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(roles)
    });

    if (res.ok) {
      alert('Roles updated!');
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl mb-4">Active Sessions</h2>
      {sessions.map(session => (
        <div key={session.session_id} className="border p-4 mb-2">
          <p><strong>Session:</strong> {session.session_id}</p>
          <p><strong>Authenticated:</strong> {session.authenticated}</p>
          <p><strong>Roles:</strong> {session.roles.join(', ')}</p>
          <input
            type="text"
            placeholder="Enter new roles (comma separated)"
            className="border p-1 mr-2"
            value={newRoles[session.session_id] || ''}
            onChange={e => handleRoleChange(session.session_id, e.target.value)}
          />
          <button
            className="px-2 py-1 border bg-gray-100"
            onClick={() => updateRoles(session.session_id)}
          >
            Update Roles
          </button>
        </div>
      ))}
    </div>
  );
}
