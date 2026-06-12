// src/context/AuthContext.jsx
import React, { createContext, useContext, useCallback, useEffect, useState } from 'react';
import { api } from '../api/client';

const AuthContext = createContext();

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const data = await api.get('/api/auth/whoami');
      if (data?.authenticated) {
        setUser({ email: data.email, user_id: data.user_id, roles: data.roles || [] });
      } else {
        setUser(null);
      }
    } catch (err) {
      console.error('Error checking auth:', err);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post('/api/auth/logout');
    } catch {
      // ignore; we clear local state regardless
    }
    setUser(null);
  }, []);

  // Check login status on mount.
  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  // The API client emits this when a refresh fails — clear local user state.
  useEffect(() => {
    const onLogout = () => setUser(null);
    window.addEventListener('auth:logout', onLogout);
    return () => window.removeEventListener('auth:logout', onLogout);
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser, loading, refreshUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
