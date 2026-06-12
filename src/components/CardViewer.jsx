import React from 'react';
import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function CardViewer() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [deckId, setDeckId] = useState('');
  const [decks, setDecks] = useState([]);
  const [flipped, setFlipped] = useState({});

  useEffect(() => {
    api.get('/api/decks').then((d) => setDecks(d.decks || [])).catch(() => {});
  }, []);

  useEffect(() => {
    const fetchCards = async () => {
      try {
        const params = new URLSearchParams();
        if (filter) params.set('label', filter);
        if (deckId) params.set('deck_id', deckId);
        const qs = params.toString();
        const data = await api.get(`/api/cards${qs ? `?${qs}` : ''}`);
        setCards(data.cards);
      } catch (err) {
        console.error(err);
        alert('Error fetching cards');
      } finally {
        setLoading(false);
      }
    };

    fetchCards();
  }, [filter, deckId]);

  const toggleFlip = (cardId) => {
    setFlipped((prev) => ({ ...prev, [cardId]: !prev[cardId] }));
  };

  if (loading) return <p className="text-center mt-8">Loading cards...</p>;

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-4 text-center">All Flashcards</h2>

      <div className="mb-4 flex justify-center gap-2">
        <input
          type="text"
          placeholder="Filter by label..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="border border-gray-300 p-2 rounded"
        />
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
      </div>

      {cards.length === 0 ? (
        <p className="text-center">No cards found.</p>
      ) : (
        <div className="space-y-4">
          {cards.map((card) => (
            <div
              key={card.card_id}
              className="bg-white border border-gray-300 rounded shadow p-4 cursor-pointer transition-transform hover:scale-105"
              onClick={() => toggleFlip(card.card_id)}
            >
              <p className="text-lg font-semibold mb-2">
                {flipped[card.card_id] ? 'Back:' : 'Front:'}
              </p>
              <p className="mb-2">{flipped[card.card_id] ? card.back : card.front}</p>
              <p className="text-sm text-gray-500">Labels: {card.labels && card.labels.join(', ')}</p>
              <p className="text-sm text-blue-500 mt-2">Click card to flip</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
