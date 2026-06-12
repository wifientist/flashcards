import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function CardAdder() {
  const { user } = useAuth();
  const isAdmin = user?.roles?.includes('admin');

  const [front, setFront] = useState('');
  const [back, setBack] = useState('');
  const [labels, setLabels] = useState('');
  const [deckId, setDeckId] = useState('');
  const [decks, setDecks] = useState([]);

  useEffect(() => {
    if (isAdmin) api.get('/api/decks').then((d) => setDecks(d.decks || [])).catch(() => {});
  }, [isAdmin]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const labelArray = labels.split(',').map(label => label.trim()).filter(label => label);

    try {
      await api.post('/api/cards', { front, back, labels: labelArray, deck_id: deckId || null });
      alert('Card created!');
      setFront('');
      setBack('');
      setLabels('');
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="max-w-md mx-auto mt-8 p-6 bg-white rounded-lg shadow-lg space-y-4"
    >
      <h2 className="text-2xl font-bold text-center mb-4">Create a New Flashcard</h2>

      {!isAdmin && (
        <p className="text-sm bg-blue-50 text-blue-800 p-2 rounded">
          🔒 This card will be private to you. You can find it under <strong>View → My cards</strong>.
        </p>
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
        <label className="block text-gray-700 mb-1">Labels (comma-separated):</label>
        <input
          type="text"
          value={labels}
          onChange={(e) => setLabels(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {isAdmin && (
        <div>
          <label className="block text-gray-700 mb-1">Deck:</label>
          <select
            value={deckId}
            onChange={(e) => setDeckId(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">— No deck —</option>
            {decks.map((d) => (
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
