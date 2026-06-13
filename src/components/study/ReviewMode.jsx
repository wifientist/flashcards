import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from '../../api/client';
import { useToast } from '../../context/ToastContext';
import { filterCards } from '../../utils/cardFilter';
import FlipCard from './FlipCard';

// FSRS grades (Again..Easy) with a short legend so it's clear which to pick.
const GRADES = [
  { rating: 'again', label: 'Again', hint: 'Forgot', desc: 'Didn’t recall it — resets, you’ll see it again soon.', cls: 'bg-red-600 hover:bg-red-700' },
  { rating: 'hard', label: 'Hard', hint: 'Struggled', desc: 'Recalled, but with real difficulty — shorter interval.', cls: 'bg-orange-500 hover:bg-orange-600' },
  { rating: 'good', label: 'Good', hint: 'Got it', desc: 'Recalled with some effort — normal interval.', cls: 'bg-green-600 hover:bg-green-700' },
  { rating: 'easy', label: 'Easy', hint: 'Instant', desc: 'Effortless — longer interval.', cls: 'bg-blue-600 hover:bg-blue-700' },
];

export default function ReviewMode({ deckIds = [], labels = [], statuses = [] }) {
  const { notify } = useToast();
  const deckKey = deckIds.join(',');
  // Key on joined values, not array identity (which changes each render).
  const labelKey = labels.join('\x1f');
  const statusKey = statuses.join('\x1f');
  const [rawQueue, setRawQueue] = useState([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [reviewed, setReviewed] = useState(0);
  const [newRemaining, setNewRemaining] = useState(0);
  const [showLegend, setShowLegend] = useState(false);

  // The label filter is applied server-side so the new-card cap (20/load) is
  // taken from label-matching cards — otherwise a chapter scope starves behind
  // unrelated new cards. Status is applied client-side below.
  const loadQueue = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (deckKey) params.set('deck_ids', deckKey);
      if (labelKey) labelKey.split('\x1f').forEach((l) => params.append('labels', l));
      const qs = params.toString();
      const data = await api.get(`/api/study/queue${qs ? `?${qs}` : ''}`);
      setRawQueue(data.queue || []);
      setNewRemaining(data.new_remaining || 0);
      setIndex(0);
      setFlipped(false);
      setReviewed(0);
    } catch (err) {
      console.error(err);
      notify('Error loading study queue', 'error');
    } finally {
      setLoading(false);
    }
  }, [deckKey, labelKey, notify]);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  // Labels are already applied server-side; only narrow by status here.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const queue = useMemo(() => filterCards(rawQueue, { statuses }), [rawQueue, statusKey]);
  useEffect(() => { setIndex(0); setFlipped(false); }, [statusKey]);

  const current = queue[index];

  const toggleFlag = async () => {
    if (!current) return;
    const next = !current.user_progress?.flagged;
    try {
      await api.put(`/api/cards/${current.card_id}/progress`, { flagged: next });
      setRawQueue((q) =>
        q.map((c) =>
          c.card_id === current.card_id
            ? { ...c, user_progress: { ...(c.user_progress || {}), flagged: next } }
            : c
        )
      );
    } catch (err) {
      console.error(err);
    }
  };

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
      notify('Error saving review', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <p className="text-center mt-8">Loading study queue…</p>;

  if (!current) {
    const moreNew = newRemaining > 0;
    return (
      <div className="text-center mt-16 space-y-4">
        <p className="text-2xl">{moreNew ? '✅ Batch done' : '🎉 All caught up!'}</p>
        <p className="text-gray-600">
          {reviewed > 0
            ? `You reviewed ${reviewed} card${reviewed === 1 ? '' : 's'}.`
            : 'Nothing due right now.'}
        </p>
        {moreNew && (
          <p className="text-gray-500 text-sm">
            {newRemaining} new card{newRemaining === 1 ? '' : 's'} left in this scope.
          </p>
        )}
        <button onClick={loadQueue} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          {moreNew ? `Introduce ${Math.min(newRemaining, 20)} more →` : 'Check again'}
        </button>
      </div>
    );
  }

  const remaining = queue.length - index;

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div className="flex items-center justify-center gap-3 text-sm text-gray-500 pt-2">
        <span>{remaining} left · {reviewed} done</span>
        <button
          onClick={toggleFlag}
          title={current.user_progress?.flagged ? 'Unstar' : 'Star this card'}
          className={`text-lg leading-none ${current.user_progress?.flagged ? 'text-amber-500' : 'text-gray-400 hover:text-amber-500'}`}
        >
          {current.user_progress?.flagged ? '★' : '☆'}
        </button>
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
