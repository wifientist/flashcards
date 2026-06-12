import React, { useState } from 'react';
import { api } from '../api/client';
import { useToast } from '../context/ToastContext';
import TagInput from './TagInput';

// Propose a change to a card. Submits to a separate proposals table — the card
// is untouched until an admin accepts.
export default function SuggestEditModal({ card, labelSuggestions = [], onClose, onSubmitted }) {
  const { notify } = useToast();
  const [front, setFront] = useState(card.front);
  const [back, setBack] = useState(card.back);
  const [labels, setLabels] = useState(card.labels || []);
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/api/cards/${card.card_id}/proposals`, { front, back, labels, note: note || null });
      notify('Change proposed — an admin will review it.', 'success');
      onSubmitted?.();
      onClose();
    } catch (err) {
      notify('Error: ' + err.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-start justify-center p-4 overflow-auto" onClick={onClose}>
      <form onClick={(e) => e.stopPropagation()} onSubmit={submit} className="bg-white rounded-lg w-full max-w-md mt-12 p-6 space-y-3">
        <h2 className="text-lg font-bold">Suggest an edit</h2>
        <p className="text-xs text-gray-500">Propose changes for an admin to review. The card won’t change until accepted.</p>

        <label className="block text-sm font-semibold">Front</label>
        <input value={front} onChange={(e) => setFront(e.target.value)} required className="w-full border p-2 rounded" />

        <label className="block text-sm font-semibold">Back</label>
        <input value={back} onChange={(e) => setBack(e.target.value)} required className="w-full border p-2 rounded" />

        <label className="block text-sm font-semibold">Labels</label>
        <TagInput tags={labels} onChange={setLabels} suggestions={labelSuggestions} />

        <label className="block text-sm font-semibold">Note (optional)</label>
        <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Why this change?" className="w-full border p-2 rounded" />

        <div className="flex justify-end gap-2 pt-1">
          <button type="button" onClick={onClose} className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300">Cancel</button>
          <button type="submit" disabled={saving} className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
            Submit proposal
          </button>
        </div>
      </form>
    </div>
  );
}
