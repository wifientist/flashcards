import React, { useState } from 'react';
import ReviewMode from './study/ReviewMode';
import BrowseMode from './study/BrowseMode';
import DeckMultiSelect from './study/DeckMultiSelect';
import { useStudyDecks } from '../hooks/useStudyDecks';

// Study section. Three modes over the same persistent deck scope:
//   Study  — the FSRS-prioritized review queue (grading)
//   Flip   — casual swipe-and-flip, no grading
//   Marked — your starred cards
export default function StudyPage() {
  const [mode, setMode] = useState('study');
  const { decks, selectedDeckIds, updateDecks } = useStudyDecks();

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
          {tab('flip', 'Flip')}
          {tab('marked', '★ Marked')}
        </div>
        <DeckMultiSelect decks={decks} selected={selectedDeckIds} onChange={updateDecks} />
      </div>

      {mode === 'study' && <ReviewMode deckIds={selectedDeckIds} />}
      {mode === 'flip' && <BrowseMode deckIds={selectedDeckIds} />}
      {mode === 'marked' && <BrowseMode marked deckIds={selectedDeckIds} />}
    </div>
  );
}
