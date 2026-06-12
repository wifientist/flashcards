import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../api/client';
import FlipCard from './FlipCard';

// FSRS grades (Again..Easy) with a short legend so it's clear which to pick.
const GRADES = [
  { rating: 'again', label: 'Again', hint: 'Forgot', desc: 'Didn’t recall it — resets, you’ll see it again soon.', cls: 'bg-red-600 hover:bg-red-700' },
  { rating: 'hard', label: 'Hard', hint: 'Struggled', desc: 'Recalled, but with real difficulty — shorter interval.', cls: 'bg-orange-500 hover:bg-orange-600' },
  { rating: 'good', label: 'Good', hint: 'Got it', desc: 'Recalled with some effort — normal interval.', cls: 'bg-green-600 hover:bg-green-700' },
  { rating: 'easy', label: 'Easy', hint: 'Instant', desc: 'Effortless — longer interval.', cls: 'bg-blue-600 hover:bg-blue-700' },
];

export default function ReviewMode({ deckId }) {
  const [queue, setQueue] = useState([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [reviewed, setReviewed] = useState(0);
  const [showLegend, setShowLegend] = useState(false);

  const loadQueue = useCallback(async () => {
    setLoading(true);
    try {
      const qs = deckId ? `?deck_id=${encodeURIComponent(deckId)}` : '';
      const data = await api.get(`/api/study/queue${qs}`);
      setQueue(data.queue || []);
      setIndex(0);
      setFlipped(false);
      setReviewed(0);
    } catch (err) {
      console.error(err);
      alert('Error loading study queue');
    } finally {
      setLoading(false);
    }
  }, [deckId]);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  const current = queue[index];

  const grade = async (rating) => {
    if (!current || submitting) return;
    setSubmitting(true);
    try {
      await api.post(`/api/cards/${current.card_id}/review`, { rating });
      setReviewed((n) => n + 1);
      setFlipped(false);
      setIndex((i) => i + 1);
    } catch (err) {
      console.error(err);
      alert('Error saving review');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <p className="text-center mt-8">Loading study queue…</p>;

  if (!current) {
    return (
      <div className="text-center mt-16 space-y-4">
        <p className="text-2xl">🎉 All caught up!</p>
        <p className="text-gray-600">
          {reviewed > 0
            ? `You reviewed ${reviewed} card${reviewed === 1 ? '' : 's'}.`
            : 'Nothing is due right now.'}
        </p>
        <button onClick={loadQueue} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Check again
        </button>
      </div>
    );
  }

  const remaining = queue.length - index;

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div className="text-center text-sm text-gray-500 pt-2">
        {remaining} left · {reviewed} done
      </div>

      <FlipCard
        key={current.card_id}
        front={current.front}
        back={current.back}
        flipped={flipped}
        onClick={() => setFlipped((f) => !f)}
        badge={(current.user_progress?.status || 'new').toUpperCase()}
      />

      <div className="px-4 pb-6 pt-2">
        {!flipped ? (
          <button
            onClick={() => setFlipped(true)}
            className="w-full max-w-2xl mx-auto block px-4 py-3 border rounded hover:bg-gray-100 transition bg-white"
          >
            Show answer
          </button>
        ) : (
          <div className="max-w-2xl mx-auto">
            <div className="grid grid-cols-4 gap-2">
              {GRADES.map((g) => (
                <button
                  key={g.rating}
                  disabled={submitting}
                  onClick={() => grade(g.rating)}
                  className={`flex flex-col items-center px-2 py-2 text-white rounded transition disabled:opacity-50 ${g.cls}`}
                >
                  <span className="font-semibold">{g.label}</span>
                  <span className="text-[10px] opacity-90">{g.hint}</span>
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowLegend((s) => !s)}
              className="mt-2 text-xs text-blue-600 hover:underline"
            >
              {showLegend ? 'Hide' : 'What do these mean?'}
            </button>
            {showLegend && (
              <ul className="mt-1 text-xs text-gray-600 space-y-1">
                {GRADES.map((g) => (
                  <li key={g.rating}>
                    <strong>{g.label}:</strong> {g.desc}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
