// src/context/AuthContext.jsx
import React, { createContext, useContext, useEffect, useState } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check login status on mount
  useEffect(() => {
    async function fetchUser() {
      try {
        const res = await fetch('/api/auth/whoami', {
          credentials: 'include',
        });
        const data = await res.json();

        if (data.authenticated) {
          setUser({
            email: data.email,
            user_id: data.user_id,
            roles: data.roles,
          });
        } else {
          setUser(null);
        }
      } catch (err) {
        console.error('Error checking auth:', err);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    fetchUser();
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser, loading }}>
      {children}
    </AuthContext.Provider>
  );
}
