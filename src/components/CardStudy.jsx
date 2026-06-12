import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

// FSRS grades. Order mirrors the difficulty scale Again..Easy.
const GRADES = [
  { rating: 'again', label: 'Again', cls: 'bg-red-600 hover:bg-red-700' },
  { rating: 'hard', label: 'Hard', cls: 'bg-orange-500 hover:bg-orange-600' },
  { rating: 'good', label: 'Good', cls: 'bg-green-600 hover:bg-green-700' },
  { rating: 'easy', label: 'Easy', cls: 'bg-blue-600 hover:bg-blue-700' },
];

export default function CardStudy() {
  const [queue, setQueue] = useState([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [reviewed, setReviewed] = useState(0);

  const loadQueue = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.get('/api/study/queue');
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
  }, []);

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

  // Queue exhausted (or empty to begin with).
  if (!current) {
    return (
      <div className="text-center mt-16 space-y-4">
        <p className="text-2xl">🎉 All caught up!</p>
        <p className="text-gray-600">
          {reviewed > 0
            ? `You reviewed ${reviewed} card${reviewed === 1 ? '' : 's'}.`
            : 'Nothing is due right now.'}
        </p>
        <button
          onClick={loadQueue}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Check again
        </button>
      </div>
    );
  }

  const remaining = queue.length - index;

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 5rem)' }}>
      <div className="text-center text-sm text-gray-500 pt-2">
        {remaining} left · {reviewed} done
      </div>

      {/* Flip card */}
      <div className="flex-1 perspective px-4 pt-2 flex items-center justify-center overflow-hidden">
        <div
          onClick={() => setFlipped((f) => !f)}
          className={`relative w-full h-full max-w-2xl mx-auto transition-transform duration-500 cursor-pointer
            ${flipped ? 'rotate-y-180' : ''}`}
          style={{ transformStyle: 'preserve-3d' }}
        >
          {/* Front */}
          <div
            className="absolute w-full h-full bg-white border rounded-lg shadow-lg flex items-center justify-center text-2xl text-center p-6"
            style={{ backfaceVisibility: 'hidden' }}
          >
            <div>{current.front}</div>
            <div className="absolute top-2 left-2 text-xs text-gray-400">
              {(current.user_progress?.status || 'new').toUpperCase()}
            </div>
          </div>

          {/* Back */}
          <div
            className="absolute w-full h-full bg-white border rounded-lg shadow-lg flex items-center justify-center text-2xl text-center p-6 rotate-y-180"
            style={{ backfaceVisibility: 'hidden' }}
          >
            <div>{current.back}</div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="px-4 pb-6 pt-2">
        {!flipped ? (
          <button
            onClick={() => setFlipped(true)}
            className="w-full max-w-2xl mx-auto block px-4 py-3 border rounded hover:bg-gray-100 transition bg-white"
          >
            Show answer
          </button>
        ) : (
          <div className="max-w-2xl mx-auto grid grid-cols-4 gap-2">
            {GRADES.map((g) => (
              <button
                key={g.rating}
                disabled={submitting}
                onClick={() => grade(g.rating)}
                className={`px-2 py-3 text-white rounded transition disabled:opacity-50 ${g.cls}`}
              >
                {g.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
