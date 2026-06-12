import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import ReviewMode from './study/ReviewMode';
import BrowseMode from './study/BrowseMode';
import DeckMultiSelect from './study/DeckMultiSelect';

// Study section host: pick a mode (Study = FSRS-prioritized queue; FlipOnly =
// swipe through cards; Marked = starred cards) and which decks to span. The
// deck scope is persisted server-side per user, so it follows you everywhere.
export default function CardStudy() {
  const [mode, setMode] = useState('study');
  const [decks, setDecks] = useState([]);
  const [selectedDeckIds, setSelectedDeckIds] = useState([]);

  useEffect(() => {
    api.get('/api/decks').then((d) => setDecks(d.decks || [])).catch(() => {});
    api.get('/api/auth/me/study-decks').then((d) => setSelectedDeckIds(d.deck_ids || [])).catch(() => {});
  }, []);

  const updateDecks = useCallback((ids) => {
    setSelectedDeckIds(ids);
    api.put('/api/auth/me/study-decks', { deck_ids: ids }).catch(() => {});
  }, []);

  const tab = (value, label) => (
    <button
      onClick={() => setMode(value)}
      className={`px-3 py-1 rounded text-sm transition ${
        mode === value ? 'bg-blue-600 text-white' : 'bg-white border hover:bg-gray-100'
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 5rem)' }}>
      <div className="flex items-center justify-center gap-3 px-4 pt-3">
        <div className="flex gap-2">
          {tab('study', 'Study')}
          {tab('browse', 'FlipOnly')}
          {tab('marked', '★ Marked')}
        </div>
        <DeckMultiSelect decks={decks} selected={selectedDeckIds} onChange={updateDecks} />
      </div>

      {mode === 'study' && <ReviewMode deckIds={selectedDeckIds} />}
      {mode === 'browse' && <BrowseMode deckIds={selectedDeckIds} />}
      {mode === 'marked' && <BrowseMode marked deckIds={selectedDeckIds} />}
    </div>
  );
}
