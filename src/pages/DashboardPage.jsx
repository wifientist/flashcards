import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';

// Ordered low → high knowledge (with the manual "difficult" flag last).
const STATUS_ORDER = ['new', 'learning', 'relearning', 'review', 'mastered', 'difficult'];

const STATUS_COLORS = {
  new: 'bg-gray-400',
  learning: 'bg-orange-400',
  relearning: 'bg-red-400',
  review: 'bg-green-500',
  mastered: 'bg-blue-500',
  difficult: 'bg-purple-500',
};

function Tile({ label, value, accent }) {
  return (
    <div className="bg-white border rounded-lg p-4 text-center shadow-sm">
      <div className={`text-3xl font-bold ${accent || 'text-gray-800'}`}>{value}</div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/api/my-progress/summary')
      .then(setSummary)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-center mt-8">Loading dashboard…</p>;
  if (error) return <p className="text-center mt-8 text-red-600">{error}</p>;

  const breakdown = summary.status_breakdown || {};
  const total = summary.total_cards || 0;

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Your Dashboard</h1>
      <p className="text-sm text-gray-500 mb-4">{summary.total_reviews} reviews logged all-time</p>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <Tile label="Total cards" value={total} />
        <Tile label="Studied" value={summary.total_cards_studied} />
        <Tile label="Due now" value={summary.due_now} accent={summary.due_now > 0 ? 'text-green-600' : 'text-gray-400'} />
        <Tile label="Starred" value={summary.starred} accent="text-amber-500" />
      </div>

      <Link
        to="/study"
        className="block text-center bg-blue-600 text-white rounded-lg py-3 mb-6 hover:bg-blue-700"
      >
        Study now →
      </Link>

      <h2 className="text-lg font-semibold mb-2">Knowledge breakdown</h2>
      {total === 0 ? (
        <p className="text-gray-500 text-sm">No cards yet.</p>
      ) : (
        <div className="space-y-2">
          {STATUS_ORDER.map((status) => {
            const count = breakdown[status] || 0;
            return (
              <div key={status} className="flex items-center gap-2 text-sm">
                <span className="w-20 text-gray-600 capitalize">{status}</span>
                <div className="flex-1 bg-gray-100 rounded h-4 overflow-hidden">
                  <div
                    className={`h-full ${STATUS_COLORS[status] || 'bg-gray-400'}`}
                    style={{ width: `${total ? (count / total) * 100 : 0}%` }}
                  />
                </div>
                <span className="w-8 text-right text-gray-600">{count}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
