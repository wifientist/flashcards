import React, { useState } from 'react';
import ReviewMode from './study/ReviewMode';
import BrowseMode from './study/BrowseMode';
import MultiSelect from './MultiSelect';
import InfoBubble from './InfoBubble';
import StudyExplainer from './StudyExplainer';
import SubscribePrompt from './SubscribePrompt';
import { useStudyFilters } from '../hooks/useStudyFilters';
import { STATUS_OPTIONS } from '../utils/cardFilter';

// Study section. Three modes over the same persistent, profile-wide filter scope
// (decks + labels + statuses, shared with the Cards page):
//   Study  — the FSRS-prioritized review queue (grading)
//   Flip   — casual swipe-and-flip, no grading
//   Marked — your starred cards
export default function StudyPage() {
  const [mode, setMode] = useState('study');
  const {
    labelOptions,
    subscribedDeckIds, selectedLabels, selectedStatuses,
    updateLabels, updateStatuses,
  } = useStudyFilters();
  const hasSubs = subscribedDeckIds.length > 0;

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

  const filters = { labels: selectedLabels, statuses: selectedStatuses };

  return (
    <div className="flex flex-col screen-below-nav">
      <div className="flex flex-wrap items-center justify-center gap-2 px-4 pt-3">
        <div className="flex gap-2">
          {tab('study', 'Study')}
          {tab('flip', 'Flip')}
          {tab('marked', '★ Marked')}
        </div>
        <MultiSelect
          label="Labels"
          allLabel="Any label"
          searchable
          options={labelOptions.map((l) => ({ value: l, label: l }))}
          selected={selectedLabels}
          onChange={updateLabels}
        />
        <MultiSelect
          label="Status"
          allLabel="Any status"
          options={STATUS_OPTIONS}
          selected={selectedStatuses}
          onChange={updateStatuses}
        />
        <InfoBubble title="How studying works · where are my cards?">
          <StudyExplainer />
        </InfoBubble>
      </div>

      {!hasSubs && mode !== 'marked' ? (
        <SubscribePrompt />
      ) : (
        <>
          {mode === 'study' && <ReviewMode deckIds={subscribedDeckIds} {...filters} />}
          {mode === 'flip' && <BrowseMode deckIds={subscribedDeckIds} {...filters} />}
          {mode === 'marked' && <BrowseMode marked deckIds={subscribedDeckIds} {...filters} />}
        </>
      )}
    </div>
  );
}
