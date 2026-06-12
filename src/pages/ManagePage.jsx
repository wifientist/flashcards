import React from 'react';
import { useSearchParams } from 'react-router-dom';
import DecksPage from './DecksPage';
import CardsPage from '../components/CardsPage';

const TABS = [
  { key: 'decks', label: 'Decks' },
  { key: 'cards', label: 'Cards' },
];

// Content management: decks and cards under one tabbed page. The active tab is
// kept in the URL (?tab=cards) so it's linkable and survives refresh.
export default function ManagePage() {
  const [params, setParams] = useSearchParams();
  const tabParam = params.get('tab');
  const active = TABS.some((t) => t.key === tabParam) ? tabParam : 'decks';

  const setTab = (key) => setParams(key === 'decks' ? {} : { tab: key }, { replace: true });

  return (
    <div>
      <div className="max-w-2xl mx-auto px-4 pt-4 flex gap-2">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-1.5 rounded text-sm transition ${
              active === t.key ? 'bg-blue-600 text-white' : 'bg-white border hover:bg-gray-100'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {active === 'decks' && <DecksPage />}
      {active === 'cards' && <CardsPage />}
    </div>
  );
}
