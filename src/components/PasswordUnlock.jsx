import React, { useState } from 'react';

export default function Unlock() {
  const [password, setPassword] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const res = await fetch('/api/auth/auth', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });

    if (res.ok) {
      alert('Authentication successful!');
    } else {
      alert('Incorrect password!');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4">
      <label>Password:</label>
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="border p-2 mx-2" />
      <button type="submit" className="px-4 py-2 border bg-gray-100">Unlock</button>
    </form>
  );
}
