import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import ReviewMode from './study/ReviewMode';
import BrowseMode from './study/BrowseMode';

// Study section host: pick a mode (Study = FSRS grading of the due queue;
// Browse = swipe through cards, no grading) and an optional deck scope.
export default function CardStudy() {
  const [mode, setMode] = useState('study');
  const [deckId, setDeckId] = useState('');
  const [decks, setDecks] = useState([]);

  useEffect(() => {
    api.get('/api/decks').then((d) => setDecks(d.decks || [])).catch(() => {});
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
        <select
          value={deckId}
          onChange={(e) => setDeckId(e.target.value)}
          className="border rounded p-1 text-sm"
        >
          <option value="">All decks</option>
          {decks.map((d) => (
            <option key={d.deck_id} value={d.deck_id}>{d.name}</option>
          ))}
        </select>
      </div>

      {mode === 'study' && <ReviewMode deckId={deckId} />}
      {mode === 'browse' && <BrowseMode deckId={deckId} />}
      {mode === 'marked' && <BrowseMode marked deckId={deckId} />}
    </div>
  );
}
