import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useStudyDecks } from '../hooks/useStudyDecks';
import BrowseMode from '../components/study/BrowseMode';
import DeckMultiSelect from '../components/study/DeckMultiSelect';

// FlipOnly landing: swipe through cards, tap to flip, no grading.
//   - logged out: featured-deck cards (the public landing)
//   - logged in: your cards, scoped to the same persistent deck selection
export default function HomePage() {
  const { user } = useAuth();
  const { decks, selectedDeckIds, updateDecks } = useStudyDecks(!!user);

  if (!user) {
    return (
      <div className="flex flex-col" style={{ height: 'calc(100vh - 5rem)' }}>
        <p className="text-center text-xs text-gray-500 pt-2">
          Swipe through the cards · <Link to="/login" className="text-blue-600 hover:underline">log in</Link> to study with spaced repetition
        </p>
        <BrowseMode featured />
      </div>
    );
  }

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 5rem)' }}>
      <div className="flex justify-center pt-3">
        <DeckMultiSelect decks={decks} selected={selectedDeckIds} onChange={updateDecks} />
      </div>
      <BrowseMode deckIds={selectedDeckIds} />
    </div>
  );
}
