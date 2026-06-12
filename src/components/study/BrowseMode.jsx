import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useSwipeable } from 'react-swipeable';
import { api } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { filterCards } from '../../utils/cardFilter';
import FlipCard from './FlipCard';

// Rapid-fire browsing: swipe left/right to move between cards, tap to flip.
// No grading / no FSRS review recorded. Sources:
//   featured -> public featured-deck cards (landing)
//   marked   -> the user's starred cards
//   else     -> all cards (optionally one deck)
// labels/statuses narrow the loaded set client-side (shared filter scope).
export default function BrowseMode({ deckIds = [], featured = false, marked = false, labels = [], statuses = [] }) {
  const { user } = useAuth();
  const { notify } = useToast();
  const deckKey = deckIds.join(',');
  const [rawCards, setRawCards] = useState([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        let base;
        if (marked) {
          base = '/api/study/marked';
          if (deckKey) params.set('deck_ids', deckKey);
        } else {
          base = '/api/cards';
          if (featured) params.set('featured', '1');
          else if (deckKey) params.set('deck_ids', deckKey);
        }
        const qs = params.toString();
        const url = `${base}${qs ? `?${qs}` : ''}`;
        const data = await api.get(url);
        setRawCards(data.cards || []);
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
  }, [deckKey, featured, marked, notify]);

  // Key on the joined values, not the array identity (which changes every render
  // from the default props and would otherwise fire the reset on each render and
  // break navigation). \x1f can't appear in a label, so it's a safe join.
  const labelKey = labels.join('\x1f');
  const statusKey = statuses.join('\x1f');
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const cards = useMemo(() => filterCards(rawCards, { labels, statuses }), [rawCards, labelKey, statusKey]);

  // Reset to the first card when the filter narrows the set.
  useEffect(() => { setIndex(0); setFlipped(false); }, [labelKey, statusKey]);

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
        setRawCards((cs) => cs.filter((c) => c.card_id !== card.card_id));
        setIndex((i) => (i > 0 ? i - 1 : 0));
        setFlipped(false);
      } else {
        setRawCards((cs) =>
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

  // index may briefly exceed the filtered length before the reset effect runs.
  const safeIndex = Math.min(index, cards.length - 1);
  const current = cards[safeIndex];
  const flagged = !!current.user_progress?.flagged;

  return (
    <div {...handlers} className="flex flex-col flex-1 min-h-0">
      <div className="flex items-center justify-center gap-3 text-sm text-gray-500 pt-2">
        <span>{safeIndex + 1} / {cards.length} · swipe or use arrows</span>
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
