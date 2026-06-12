import React, { useEffect, useState } from 'react';
import { api } from '../api/client';

const STATUS_STYLE = {
  pending: 'bg-amber-100 text-amber-800',
  accepted: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
};

const FILTERS = ['all', 'pending', 'accepted', 'rejected'];

export default function ProposalsPage() {
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/api/my-proposals')
      .then((d) => setProposals(d.proposals || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-center mt-8">Loading…</p>;
  if (error) return <p className="text-center mt-8 text-red-600">{error}</p>;

  const shown = filter === 'all' ? proposals : proposals.filter((p) => p.status === filter);

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">My proposed changes</h1>
      <p className="text-sm text-gray-500 mb-4">Edits you’ve suggested to cards, and how they were reviewed.</p>

      <div className="flex gap-2 mb-4 text-sm">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded capitalize ${filter === f ? 'bg-blue-600 text-white' : 'bg-white border hover:bg-gray-100'}`}
          >
            {f}
          </button>
        ))}
      </div>

      {shown.length === 0 ? (
        <p className="text-center text-gray-500">No proposals{filter !== 'all' ? ` (${filter})` : ''}.</p>
      ) : (
        <div className="space-y-3">
          {shown.map((p) => (
            <div key={p.id} className="border rounded p-4 bg-white">
              <div className="flex justify-between items-center mb-2">
                <span className={`text-xs px-2 py-0.5 rounded ${STATUS_STYLE[p.status] || ''}`}>{p.status}</span>
                <span className="text-xs text-gray-400">
                  {p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-gray-400 mb-1">Current</p>
                  {p.current ? (
                    <>
                      <p><strong>{p.current.front}</strong> → {p.current.back}</p>
                      {p.current.labels?.length > 0 && <p className="text-xs text-gray-500">{p.current.labels.join(', ')}</p>}
                    </>
                  ) : <p className="text-gray-400">card removed</p>}
                </div>
                <div>
                  <p className="text-xs text-gray-400 mb-1">Proposed</p>
                  <p><strong>{p.proposed.front}</strong> → {p.proposed.back}</p>
                  {p.proposed.labels?.length > 0 && <p className="text-xs text-gray-500">{p.proposed.labels.join(', ')}</p>}
                </div>
              </div>
              {p.note && <p className="text-xs text-gray-500 mt-2">Note: {p.note}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
