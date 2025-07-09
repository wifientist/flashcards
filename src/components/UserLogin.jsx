import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext'; 

export default function UserLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();

    const res = await fetch('/api/auth/login', {
      method: 'POST',
      credentials: 'include',  // This allows cookies to be stored (for JWT/session)
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (res.ok) {
      const data = await res.json();
      console.log('Login successful:', data);
      setUser({
        email: data.user.email,
        user_id: data.user.user_id,
        roles: data.user.roles,
      });
      navigate('/study');
    } else {
      const error = await res.json();
      alert(`Login failed: ${error.detail || 'Unknown error'}`);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 flex flex-col max-w-sm mx-auto space-y-4">
      <div>
        <label className="block mb-1 font-semibold">Email:</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border p-2 rounded"
          required
        />
      </div>
      <div>
        <label className="block mb-1 font-semibold">Password:</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border p-2 rounded"
          required
        />
      </div>
      <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
        Log In
      </button>
    </form>
  );
}
