import React, { useState, useEffect, useCallback } from 'react';
import { useSwipeable } from 'react-swipeable';
import { api } from '../../api/client';
import FlipCard from './FlipCard';

// Rapid-fire browsing: swipe left/right to move between cards, tap to flip.
// No grading and no FSRS review is recorded — this is just for quick passes.
// `featured` scopes to public/featured-deck cards (used by the public landing).
export default function BrowseMode({ deckId, featured = false }) {
  const [cards, setCards] = useState([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (featured) params.set('featured', '1');
        else if (deckId) params.set('deck_id', deckId);
        const qs = params.toString();
        const data = await api.get(`/api/cards${qs ? `?${qs}` : ''}`);
        setCards(data.cards || []);
        setIndex(0);
        setFlipped(false);
      } catch (err) {
        console.error(err);
        alert('Error loading cards');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [deckId, featured]);

  const move = useCallback(
    (delta) => {
      setFlipped(false);
      setIndex((i) => {
        if (!cards.length) return 0;
        return (i + delta + cards.length) % cards.length;
      });
    },
    [cards.length]
  );

  const handlers = useSwipeable({
    onSwipedLeft: () => move(1),
    onSwipedRight: () => move(-1),
    trackMouse: true,
    preventScrollOnSwipe: true,
  });

  if (loading) return <p className="text-center mt-8">Loading cards…</p>;
  if (!cards.length) return <p className="text-center mt-8">No cards to browse.</p>;

  const current = cards[index];

  return (
    <div {...handlers} className="flex flex-col flex-1 min-h-0">
      <div className="text-center text-sm text-gray-500 pt-2">
        {index + 1} / {cards.length} · swipe or use arrows
      </div>

      <FlipCard
        front={current.front}
        back={current.back}
        flipped={flipped}
        onClick={() => setFlipped((f) => !f)}
        badge={current.labels?.length ? current.labels.join(' · ') : null}
      />

      <div className="px-4 pb-6 pt-2 flex justify-between max-w-2xl mx-auto w-full">
        <button onClick={() => move(-1)} className="px-4 py-2 border rounded hover:bg-gray-100 bg-white">
          ⬅️ Prev
        </button>
        <button onClick={() => move(1)} className="px-4 py-2 border rounded hover:bg-gray-100 bg-white">
          Next ➡️
        </button>
      </div>
    </div>
  );
}
