import React, { useState, useEffect, useCallback } from 'react';
import { useSwipeable } from 'react-swipeable';
import { api } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import FlipCard from './FlipCard';

// Rapid-fire browsing: swipe left/right to move between cards, tap to flip.
// No grading / no FSRS review recorded. Sources:
//   featured -> public featured-deck cards (landing)
//   marked   -> the user's starred cards
//   else     -> all cards (optionally one deck)
export default function BrowseMode({ deckId, featured = false, marked = false }) {
  const { user } = useAuth();
  const { notify } = useToast();
  const [cards, setCards] = useState([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        let url;
        if (marked) {
          url = '/api/study/marked';
        } else {
          const params = new URLSearchParams();
          if (featured) params.set('featured', '1');
          else if (deckId) params.set('deck_id', deckId);
          const qs = params.toString();
          url = `/api/cards${qs ? `?${qs}` : ''}`;
        }
        const data = await api.get(url);
        setCards(data.cards || []);
        setIndex(0);
        setFlipped(false);
      } catch (err) {
        console.error(err);
        notify('Error loading cards', 'error');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [deckId, featured, marked, notify]);

  const move = useCallback(
    (delta) => {
      setFlipped(false);
      setIndex((i) => (cards.length ? (i + delta + cards.length) % cards.length : 0));
    },
    [cards.length]
  );

  const toggleFlag = async () => {
    const card = cards[index];
    if (!card) return;
    const next = !card.user_progress?.flagged;
    try {
      await api.put(`/api/cards/${card.card_id}/progress`, { flagged: next });
      if (marked && !next) {
        // Unstarred in the Marked view → drop it from the list.
        setCards((cs) => cs.filter((c) => c.card_id !== card.card_id));
        setIndex((i) => (i > 0 ? i - 1 : 0));
        setFlipped(false);
      } else {
        setCards((cs) =>
          cs.map((c) =>
            c.card_id === card.card_id
              ? { ...c, user_progress: { ...(c.user_progress || {}), flagged: next } }
              : c
          )
        );
      }
    } catch (err) {
      console.error(err);
      notify('Error updating star', 'error');
    }
  };

  const handlers = useSwipeable({
    onSwipedLeft: () => move(1),
    onSwipedRight: () => move(-1),
    trackMouse: true,
    preventScrollOnSwipe: true,
  });

  if (loading) return <p className="text-center mt-8">Loading cards…</p>;
  if (!cards.length) {
    return (
      <p className="text-center mt-8">
        {marked ? 'No starred cards yet — tap ☆ while studying to mark one.' : 'No cards to browse.'}
      </p>
    );
  }

  const current = cards[index];
  const flagged = !!current.user_progress?.flagged;

  return (
    <div {...handlers} className="flex flex-col flex-1 min-h-0">
      <div className="flex items-center justify-center gap-3 text-sm text-gray-500 pt-2">
        <span>{index + 1} / {cards.length} · swipe or use arrows</span>
        {user && (
          <button
            onClick={toggleFlag}
            title={flagged ? 'Unstar' : 'Star this card'}
            className={`text-lg leading-none ${flagged ? 'text-amber-500' : 'text-gray-400 hover:text-amber-500'}`}
          >
            {flagged ? '★' : '☆'}
          </button>
        )}
      </div>

      <FlipCard
        key={current.card_id}
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
