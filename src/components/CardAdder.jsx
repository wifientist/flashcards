import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import TagInput from './TagInput';

export default function CardAdder({ onCreated, deck } = {}) {
  const { user } = useAuth();
  const { notify } = useToast();
  const isAdmin = user?.roles?.includes('admin');
  // Targeted mode: adding directly into a specific deck (from the Decks page).
  const targeted = !!deck;
  const targetPrivate = targeted && !!deck.owner_id;

  const [front, setFront] = useState('');
  const [back, setBack] = useState('');
  const [labels, setLabels] = useState([]);
  const [labelSuggestions, setLabelSuggestions] = useState([]);
  const [deckId, setDeckId] = useState('');
  const [decks, setDecks] = useState([]);
  // Admins choose: public app card vs their own private card.
  const [makePrivate, setMakePrivate] = useState(false);

  useEffect(() => {
    api.get('/api/decks').then((d) => setDecks(d.decks || [])).catch(() => {});
    api.get('/api/labels').then((d) => setLabelSuggestions((d.labels || []).map((l) => l.label))).catch(() => {});
  }, []);

  // Public cards (admin) can be filed into a public deck; private cards always
  // land in the user's auto "My Cards" deck, so no deck choice there.
  const asPublic = isAdmin && !makePrivate;
  const publicDecks = decks.filter((d) => !d.owner_id);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const body = targeted
        ? { front, back, labels, private: targetPrivate, deck_id: targetPrivate ? null : deck.deck_id }
        : { front, back, labels, deck_id: asPublic ? (deckId || null) : null, private: isAdmin ? makePrivate : true };
      await api.post('/api/cards', body);
      notify('Card created!', 'success');
      setFront('');
      setBack('');
      setLabels([]);
      setDeckId('');
      if (onCreated) onCreated();
    } catch (err) {
      notify('Error: ' + err.message, 'error');
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`bg-white space-y-4 ${targeted ? 'p-6' : 'max-w-md mx-auto mt-8 p-6 rounded-lg shadow-lg'}`}
    >
      <h2 className="text-2xl font-bold text-center mb-4">
        {targeted ? `Add a card to ${deck.name}` : 'Create a New Flashcard'}
      </h2>

      {!targeted && !isAdmin && (
        <p className="text-sm bg-blue-50 text-blue-800 p-2 rounded">
          🔒 This card will be private to you. Find it under <strong>Cards</strong> → the <strong>“My Cards”</strong> deck filter.
        </p>
      )}

      {!targeted && isAdmin && (
        <div>
          <label className="block text-gray-700 mb-1">Card type:</label>
          <div className="flex gap-4 text-sm">
            <label className="flex items-center gap-1 cursor-pointer">
              <input type="radio" checked={!makePrivate} onChange={() => setMakePrivate(false)} />
              <span>Public (app card)</span>
            </label>
            <label className="flex items-center gap-1 cursor-pointer">
              <input type="radio" checked={makePrivate} onChange={() => setMakePrivate(true)} />
              <span>🔒 Private (my card)</span>
            </label>
          </div>
        </div>
      )}

      <div>
        <label className="block text-gray-700 mb-1">Front:</label>
        <input
          type="text"
          value={front}
          onChange={(e) => setFront(e.target.value)}
          required
          className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-gray-700 mb-1">Back:</label>
        <input
          type="text"
          value={back}
          onChange={(e) => setBack(e.target.value)}
          required
          className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-gray-700 mb-1">Labels:</label>
        <TagInput tags={labels} onChange={setLabels} suggestions={labelSuggestions} />
      </div>

      {!targeted && asPublic && (
        <div>
          <label className="block text-gray-700 mb-1">Deck:</label>
          <select
            value={deckId}
            onChange={(e) => setDeckId(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">— No deck —</option>
            {publicDecks.map((d) => (
              <option key={d.deck_id} value={d.deck_id}>{d.name}</option>
            ))}
          </select>
        </div>
      )}

      <button
        type="submit"
        className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 transition-colors"
      >
        Create Card
      </button>
    </form>
  );
}
