import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import BrowseMode from '../components/study/BrowseMode';

// Public landing: anyone (logged in or not) can swipe through the featured-deck
// cards. No login, no tracking — just browse. Admins choose which decks are
// featured on the Decks page.
export default function HomePage() {
  const { user } = useAuth();

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 5rem)' }}>
      {!user && (
        <p className="text-center text-xs text-gray-500 pt-2">
          Swipe through the cards · <Link to="/login" className="text-blue-600 hover:underline">log in</Link> to track progress and study with spaced repetition
        </p>
      )}
      <BrowseMode featured />
    </div>
  );
}
