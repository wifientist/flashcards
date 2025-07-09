import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function LogoutButton({ onLogout }) {
  const navigate = useNavigate();
  const handleLogout = async () => {
    const res = await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    });

    if (res.ok) {
      alert('Logged out successfully.');
      if (onLogout) onLogout(); // Optional callback to update parent state
      navigate('/');
    } else {
      alert('Logout failed.');
    }
  };

  return (
    <button
      onClick={handleLogout}
      className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
    >
      Log Out
    </button>
  );
}
