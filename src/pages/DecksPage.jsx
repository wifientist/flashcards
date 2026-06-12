import React, { useEffect, useState, useCallback } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function DecksPage() {
  const { user } = useAuth();
  const isAdmin = user?.roles?.includes('admin');

  const [decks, setDecks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.get('/api/decks');
      setDecks(data.decks || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const createDeck = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/api/decks', { name, description: description || null });
      setName('');
      setDescription('');
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteDeck = async (deckId) => {
    if (!window.confirm('Delete this deck? Its cards are kept but unfiled.')) return;
    try {
      await api.del(`/api/decks/${deckId}`);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  // Export downloads a file, so use a raw blob fetch (not the JSON client).
  const exportCards = async (deckId, format) => {
    const params = new URLSearchParams({ format });
    if (deckId) params.set('deck_id', deckId);
    try {
      const res = await fetch(`/api/export/cards?${params}`, { credentials: 'include' });
      if (!res.ok) throw new Error(`Export failed (${res.status})`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cards.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    }
  };

  const importToDeck = async (deckId, file) => {
    if (!file) return;
    const format = file.name.toLowerCase().endsWith('.csv') ? 'csv' : 'json';
    try {
      const content = await file.text();
      const res = await api.post('/api/import/cards', { format, content, deck_id: deckId || null });
      alert(`Imported ${res.imported} card(s)${res.skipped ? `, skipped ${res.skipped}` : ''}.`);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <p className="text-center mt-8">Loading decks…</p>;

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Decks</h1>
        {user && (
          <div className="text-sm space-x-2">
            <span className="text-gray-500">Export all:</span>
            <button onClick={() => exportCards('', 'csv')} className="text-blue-600 hover:underline">CSV</button>
            <button onClick={() => exportCards('', 'json')} className="text-blue-600 hover:underline">JSON</button>
          </div>
        )}
      </div>
      {error && <div className="bg-red-100 text-red-800 text-sm p-2 rounded mb-4">{error}</div>}

      {isAdmin && (
        <form onSubmit={createDeck} className="bg-white border rounded p-4 mb-6 space-y-2">
          <h2 className="font-semibold">New deck</h2>
          <input
            type="text"
            placeholder="Deck name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full border p-2 rounded"
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full border p-2 rounded"
          />
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            Create deck
          </button>
        </form>
      )}

      {decks.length === 0 ? (
        <p className="text-center text-gray-500">No decks yet.</p>
      ) : (
        <div className="space-y-2">
          {decks.map((deck) => (
            <div key={deck.deck_id} className="border rounded p-4 flex justify-between items-start bg-white">
              <div>
                <p className="font-semibold">{deck.name}</p>
                {deck.description && <p className="text-sm text-gray-600">{deck.description}</p>}
                <p className="text-xs text-gray-400 mt-1">{deck.card_count} cards</p>
              </div>
              <div className="flex flex-col items-end gap-1 text-sm">
                {user && (
                  <div className="space-x-2">
                    <button onClick={() => exportCards(deck.deck_id, 'csv')} className="text-blue-600 hover:underline">Export CSV</button>
                    <button onClick={() => exportCards(deck.deck_id, 'json')} className="text-blue-600 hover:underline">JSON</button>
                  </div>
                )}
                {isAdmin && (
                  <label className="text-green-700 hover:underline cursor-pointer">
                    Import…
                    <input
                      type="file"
                      accept=".csv,.json"
                      className="hidden"
                      onChange={(e) => {
                        importToDeck(deck.deck_id, e.target.files[0]);
                        e.target.value = '';
                      }}
                    />
                  </label>
                )}
                {isAdmin && (
                  <button onClick={() => deleteDeck(deck.deck_id)} className="text-red-600 hover:underline">
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
