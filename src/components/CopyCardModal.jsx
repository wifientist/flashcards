import React, { useState } from 'react';
import { api } from '../api/client';
import { useToast } from '../context/ToastContext';
import TagInput from './TagInput';

// Admin: copy a (private) card into the public pool, with the chance to edit any
// field and pick a target public deck on the way in. Creates a NEW public card;
// the original is untouched.
export default function CopyCardModal({ card, publicDecks = [], labelSuggestions = [], onClose, onCopied }) {
  const { notify } = useToast();
  const [front, setFront] = useState(card.front);
  const [back, setBack] = useState(card.back);
  const [labels, setLabels] = useState(card.labels || []);
  const [deckId, setDeckId] = useState('');
  const [saving, setSaving] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/api/cards', {
        front, back, labels, private: false, deck_id: deckId || null,
      });
      notify('Copied to public.', 'success');
      onCopied?.();
      onClose();
    } catch (err) {
      notify('Error: ' + err.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-start justify-center p-4 overflow-auto" onClick={onClose}>
      <form
        onClick={(e) => e.stopPropagation()}
        onSubmit={submit}
        className="bg-white rounded-lg w-full max-w-md mt-12 p-6 space-y-3"
      >
        <h2 className="text-lg font-bold">Copy to public</h2>
        {card.owner_email && (
          <p className="text-xs text-gray-500">from {card.owner_email}'s private cards — edit anything before publishing.</p>
        )}

        <label className="block text-sm font-semibold">Front</label>
        <input value={front} onChange={(e) => setFront(e.target.value)} required className="w-full border p-2 rounded" />

        <label className="block text-sm font-semibold">Back</label>
        <input value={back} onChange={(e) => setBack(e.target.value)} required className="w-full border p-2 rounded" />

        <label className="block text-sm font-semibold">Labels</label>
        <TagInput tags={labels} onChange={setLabels} suggestions={labelSuggestions} />

        <label className="block text-sm font-semibold">Public deck</label>
        <select value={deckId} onChange={(e) => setDeckId(e.target.value)} className="w-full border p-2 rounded">
          <option value="">— No deck —</option>
          {publicDecks.map((d) => (
            <option key={d.deck_id} value={d.deck_id}>{d.name}</option>
          ))}
        </select>

        <div className="flex justify-end gap-2 pt-1">
          <button type="button" onClick={onClose} className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300">Cancel</button>
          <button type="submit" disabled={saving} className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
            Create public card
          </button>
        </div>
      </form>
    </div>
  );
}
