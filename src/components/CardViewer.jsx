import React, { useEffect, useState, useCallback } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import TagInput from './TagInput';

export default function CardViewer() {
  const { user } = useAuth();
  const { notify } = useToast();
  const isAdmin = user?.roles?.includes('admin');

  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [deckId, setDeckId] = useState('');
  const [decks, setDecks] = useState([]);
  const [labelSuggestions, setLabelSuggestions] = useState([]);
  const [scope, setScope] = useState('all'); // 'all' | 'mine'
  const [flipped, setFlipped] = useState({});
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ front: '', back: '', labels: [], deck_id: '' });
  const [error, setError] = useState('');

  const canModify = (card) =>
    isAdmin || (card.owner_id && card.owner_id === user?.user_id);

  useEffect(() => {
    api.get('/api/decks').then((d) => setDecks(d.decks || [])).catch(() => {});
    api.get('/api/labels').then((d) => setLabelSuggestions((d.labels || []).map((l) => l.label))).catch(() => {});
  }, []);

  const deckName = useCallback(
    (id) => decks.find((d) => d.deck_id === id)?.name || null,
    [decks]
  );

  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filter) params.set('label', filter);
      if (scope === 'mine') params.set('mine', '1');
      else if (deckId) params.set('deck_id', deckId);
      const qs = params.toString();
      const data = await api.get(`/api/cards${qs ? `?${qs}` : ''}`);
      setCards(data.cards);
    } catch (err) {
      console.error(err);
      setError('Error fetching cards');
    } finally {
      setLoading(false);
    }
  }, [filter, deckId, scope]);

  useEffect(() => {
    load();
  }, [load]);

  const copyToPublic = async (cardId) => {
    setError('');
    try {
      await api.post(`/api/cards/${cardId}/copy`);
      notify('Copied to the public pool. File it into a deck via Edit.', 'success');
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleFlip = (cardId) => {
    setFlipped((prev) => ({ ...prev, [cardId]: !prev[cardId] }));
  };

  const startEdit = (card) => {
    setEditingId(card.card_id);
    setEditForm({
      front: card.front,
      back: card.back,
      labels: card.labels || [],
      deck_id: card.deck_id || '',
    });
  };

  const saveEdit = async (cardId) => {
    setError('');
    try {
      await api.put(`/api/cards/${cardId}`, {
        front: editForm.front,
        back: editForm.back,
        labels: editForm.labels,
        deck_id: editForm.deck_id || null,
      });
      setEditingId(null);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteCard = async (cardId) => {
    if (!window.confirm('Delete this card? This also removes everyone’s progress on it.')) return;
    setError('');
    try {
      await api.del(`/api/cards/${cardId}`);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <p className="text-center mt-8">Loading cards...</p>;

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-4 text-center">All Flashcards</h2>
      {error && <div className="bg-red-100 text-red-800 text-sm p-2 rounded mb-4">{error}</div>}

      <div className="mb-4 flex justify-center gap-2 flex-wrap">
        <input
          type="text"
          placeholder="Filter by label..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="border border-gray-300 p-2 rounded"
        />
        {scope === 'all' && (
          <select
            value={deckId}
            onChange={(e) => setDeckId(e.target.value)}
            className="border border-gray-300 p-2 rounded"
          >
            <option value="">All decks</option>
            {decks.map((d) => (
              <option key={d.deck_id} value={d.deck_id}>{d.name}</option>
            ))}
          </select>
        )}
        {user && (
          <select
            value={scope}
            onChange={(e) => setScope(e.target.value)}
            className="border border-gray-300 p-2 rounded"
          >
            <option value="all">All cards</option>
            <option value="mine">My cards</option>
          </select>
        )}
      </div>

      {cards.length === 0 ? (
        <p className="text-center">No cards found.</p>
      ) : (
        <div className="space-y-4">
          {cards.map((card) =>
            editingId === card.card_id ? (
              <CardEditForm
                key={card.card_id}
                form={editForm}
                setForm={setEditForm}
                decks={decks.filter((d) => (card.owner_id ? d.owner_id === user?.user_id : !d.owner_id))}
                allowDeck={canModify(card)}
                labelSuggestions={labelSuggestions}
                onSave={() => saveEdit(card.card_id)}
                onCancel={() => setEditingId(null)}
              />
            ) : (
              <div key={card.card_id} className="bg-white border border-gray-300 rounded shadow p-4">
                <div className="cursor-pointer" onClick={() => toggleFlip(card.card_id)}>
                  <p className="text-lg font-semibold mb-2">
                    {flipped[card.card_id] ? 'Back:' : 'Front:'}
                    {card.owner_id && (
                      <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded align-middle">
                        🔒 Private
                      </span>
                    )}
                  </p>
                  <p className="mb-2">{flipped[card.card_id] ? card.back : card.front}</p>
                  <div className="flex flex-wrap gap-1 items-center text-sm text-gray-500">
                    {card.labels?.map((l) => (
                      <button
                        key={l}
                        onClick={(e) => { e.stopPropagation(); setFilter(l); }}
                        title={`Filter by ${l}`}
                        className="bg-gray-100 hover:bg-blue-100 text-gray-700 rounded px-2 py-0.5 text-xs"
                      >
                        #{l}
                      </button>
                    ))}
                    {deckName(card.deck_id) && <span className="text-xs">· Deck: {deckName(card.deck_id)}</span>}
                  </div>
                  <p className="text-xs text-blue-500 mt-2">Click to flip</p>
                </div>
                {(canModify(card) || (isAdmin && card.owner_id)) && (
                  <div className="mt-3 pt-2 border-t flex gap-3 text-sm">
                    {canModify(card) && (
                      <button onClick={() => startEdit(card)} className="text-blue-600 hover:underline">
                        Edit
                      </button>
                    )}
                    {canModify(card) && (
                      <button onClick={() => deleteCard(card.card_id)} className="text-red-600 hover:underline">
                        Delete
                      </button>
                    )}
                    {isAdmin && card.owner_id && (
                      <button onClick={() => copyToPublic(card.card_id)} className="text-green-700 hover:underline">
                        Copy to public
                      </button>
                    )}
                  </div>
                )}
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
}

function CardEditForm({ form, setForm, decks, allowDeck, labelSuggestions, onSave, onCancel }) {
  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  return (
    <div className="bg-white border border-blue-300 rounded shadow p-4 space-y-2">
      <label className="block text-sm font-semibold">Front</label>
      <input value={form.front} onChange={set('front')} className="w-full border p-2 rounded" />
      <label className="block text-sm font-semibold">Back</label>
      <input value={form.back} onChange={set('back')} className="w-full border p-2 rounded" />
      <label className="block text-sm font-semibold">Labels</label>
      <TagInput
        tags={form.labels}
        onChange={(labels) => setForm((f) => ({ ...f, labels }))}
        suggestions={labelSuggestions}
      />
      {allowDeck && (
        <>
          <label className="block text-sm font-semibold">Deck</label>
          <select value={form.deck_id} onChange={set('deck_id')} className="w-full border p-2 rounded">
            <option value="">— No deck —</option>
            {decks.map((d) => (
              <option key={d.deck_id} value={d.deck_id}>{d.name}</option>
            ))}
          </select>
        </>
      )}
      <div className="flex gap-2 justify-end pt-1">
        <button onClick={onCancel} className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300">Cancel</button>
        <button onClick={onSave} className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">Save</button>
      </div>
    </div>
  );
}
