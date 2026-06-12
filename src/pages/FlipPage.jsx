import React from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import BrowseMode from '../components/study/BrowseMode';

// Public landing: logged-out visitors swipe through the featured deck and are
// nudged to log in. Logged-in users study (Flip is now a mode on the Study page).
export default function FlipPage() {
  const { user } = useAuth();

  if (user) return <Navigate to="/study" replace />;

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 5rem)' }}>
      <p className="text-center text-xs text-gray-500 pt-2">
        Swipe through the cards · <Link to="/login" className="text-blue-600 hover:underline">log in</Link> to study with spaced repetition
      </p>
      <BrowseMode featured />
    </div>
  );
}
