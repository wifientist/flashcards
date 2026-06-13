import React, { useEffect, useState, useCallback } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useStudyFilters } from '../hooks/useStudyFilters';
import { STATUS_OPTIONS, filterCards } from '../utils/cardFilter';
import TagInput from './TagInput';
import CardAdder from './CardAdder';
import CopyCardModal from './CopyCardModal';
import SuggestEditModal from './SuggestEditModal';
import DeckMultiSelect from './study/DeckMultiSelect';
import MultiSelect from './MultiSelect';

export default function CardsPage() {
  const { user } = useAuth();
  const isAdmin = user?.roles?.includes('admin');
  const canCreate = user?.roles?.some((r) => r === 'admin' || r === 'trusted');
  const [showCreate, setShowCreate] = useState(false);
  const [copyTarget, setCopyTarget] = useState(null);
  const [suggestTarget, setSuggestTarget] = useState(null);

  // Filter scope (decks + labels + statuses) is shared with Study and persisted
  // per profile.
  const {
    decks, reloadDecks, labelOptions, reloadLabels,
    selectedDeckIds, selectedLabels, selectedStatuses,
    updateDecks, updateLabels, updateStatuses,
  } = useStudyFilters(!!user);

  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [flipped, setFlipped] = useState({});
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ front: '', back: '', labels: [], deck_id: '' });
  const [error, setError] = useState('');

  const canModify = (card) =>
    isAdmin || (card.owner_id && card.owner_id === user?.user_id);

  const toggleLabel = (l) =>
    updateLabels(selectedLabels.includes(l) ? selectedLabels.filter((x) => x !== l) : [...selectedLabels, l]);

  const deckName = useCallback(
    (id) => decks.find((d) => d.deck_id === id)?.name || null,
    [decks]
  );

  const deckKey = selectedDeckIds.join(',');
  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (deckKey) params.set('deck_ids', deckKey);
      const qs = params.toString();
      const data = await api.get(`/api/cards${qs ? `?${qs}` : ''}`);
      setCards(data.cards);
    } catch (err) {
      console.error(err);
      setError('Error fetching cards');
    } finally {
      setLoading(false);
    }
  }, [deckKey]);

  useEffect(() => {
    load();
  }, [load]);

  const toggleFlip = (cardId) => {
    setFlipped((prev) => ({ ...prev, [cardId]: !prev[cardId] }));
  };

  const startEdit = (card) => {
    setEditingId(card.card_id);
    setEditForm({
      front: card.front,
      back: card.back,
      labels: card.labels || [],
      deck_id: card.deck_id || '',
    });
  };

  const saveEdit = async (cardId) => {
    setError('');
    try {
      await api.put(`/api/cards/${cardId}`, {
        front: editForm.front,
        back: editForm.back,
        labels: editForm.labels,
        deck_id: editForm.deck_id || null,
      });
      setEditingId(null);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteCard = async (cardId) => {
    if (!window.confirm('Delete this card? This also removes everyone’s progress on it.')) return;
    setError('');
    try {
      await api.del(`/api/cards/${cardId}`);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const visibleCards = filterCards(cards, { statuses: selectedStatuses, labels: selectedLabels });

  if (loading) return <p className="text-center mt-8">Loading cards...</p>;

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-4 text-center">All Flashcards</h2>
      {error && <div className="bg-red-100 text-red-800 text-sm p-2 rounded mb-4">{error}</div>}

      {canCreate && (
        <div className="mb-4 text-center">
          <button
            onClick={() => setShowCreate((s) => !s)}
            className="text-sm text-blue-600 hover:underline"
          >
            {showCreate ? '× Close' : '+ New card'}
          </button>
          {showCreate && <CardAdder onCreated={() => { load(); reloadDecks(); reloadLabels(); }} />}
        </div>
      )}

      <div className="mb-4 flex justify-center items-center gap-2 flex-wrap">
        <DeckMultiSelect decks={decks} selected={selectedDeckIds} onChange={updateDecks} />
        <MultiSelect
          label="Labels"
          allLabel="Any label"
          searchable
          options={labelOptions.map((l) => ({ value: l, label: l }))}
          selected={selectedLabels}
          onChange={updateLabels}
        />
        {user && (
          <MultiSelect
            label="Status"
            allLabel="Any status"
            options={STATUS_OPTIONS}
            selected={selectedStatuses}
            onChange={updateStatuses}
          />
        )}
      </div>

      <p className="text-center text-xs text-gray-500 mb-3">
        {visibleCards.length === cards.length
          ? `${cards.length} card${cards.length === 1 ? '' : 's'}`
          : `${visibleCards.length} of ${cards.length} cards match`}
      </p>

      {visibleCards.length === 0 ? (
        <p className="text-center">No cards found.</p>
      ) : (
        <div className="space-y-4">
          {visibleCards.map((card) =>
            editingId === card.card_id ? (
              <CardEditForm
                key={card.card_id}
                form={editForm}
                setForm={setEditForm}
                decks={decks.filter((d) => !d.owner_id)}
                allowDeck={isAdmin && !card.owner_id}
                labelSuggestions={labelOptions}
                onSave={() => saveEdit(card.card_id)}
                onCancel={() => setEditingId(null)}
              />
            ) : (
              <div key={card.card_id} className="bg-white border border-gray-300 rounded shadow p-4">
                <div className="cursor-pointer" onClick={() => toggleFlip(card.card_id)}>
                  <div className="flex justify-between items-start gap-2 mb-2">
                    <p className="text-lg font-semibold">
                      {flipped[card.card_id] ? 'Back:' : 'Front:'}
                      <span className="ml-2 text-xs font-normal text-blue-500 align-middle">Click to flip</span>
                      {card.owner_id && (
                        <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded align-middle">
                          🔒 {card.owner_email || 'Private'}
                        </span>
                      )}
                    </p>
                    {user && card.user_progress && (
                      <div className="text-right shrink-0">
                        <span className="text-xs font-medium uppercase bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                          {card.user_progress.status || 'new'}
                        </span>
                        {(card.user_progress.review_count > 0 || card.user_progress.flagged) && (
                          <p className="text-xs text-gray-500 mt-0.5">
                            {card.user_progress.review_count > 0 && <>{card.user_progress.review_count}× reviewed</>}
                            {card.user_progress.flagged && <> · ★</>}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                  <p className="mb-2">{flipped[card.card_id] ? card.back : card.front}</p>
                  <div className="flex flex-wrap gap-1 items-center text-sm text-gray-500">
                    {card.labels?.map((l) => (
                      <button
                        key={l}
                        onClick={(e) => { e.stopPropagation(); toggleLabel(l); }}
                        title={`Filter by ${l}`}
                        className="bg-gray-100 hover:bg-blue-100 text-gray-700 rounded px-2 py-0.5 text-xs"
                      >
                        #{l}
                      </button>
                    ))}
                    {deckName(card.deck_id) && <span className="text-xs">· Deck: {deckName(card.deck_id)}</span>}
                  </div>
                </div>
                {user && (
                  <div className="mt-3 pt-2 border-t flex gap-3 text-sm">
                    {canModify(card) && (
                      <button onClick={() => startEdit(card)} className="text-blue-600 hover:underline">
                        Edit
                      </button>
                    )}
                    {canModify(card) && (
                      <button onClick={() => deleteCard(card.card_id)} className="text-red-600 hover:underline">
                        Delete
                      </button>
                    )}
                    {!canModify(card) && (
                      <button onClick={() => setSuggestTarget(card)} className="text-blue-600 hover:underline">
                        Suggest edit
                      </button>
                    )}
                    {isAdmin && card.owner_id && (
                      <button onClick={() => setCopyTarget(card)} className="text-green-700 hover:underline">
                        Copy to public…
                      </button>
                    )}
                  </div>
                )}
              </div>
            )
          )}
        </div>
      )}

      {copyTarget && (
        <CopyCardModal
          card={copyTarget}
          publicDecks={decks.filter((d) => !d.owner_id)}
          labelSuggestions={labelOptions}
          onClose={() => setCopyTarget(null)}
          onCopied={() => { load(); reloadDecks(); }}
        />
      )}

      {suggestTarget && (
        <SuggestEditModal
          card={suggestTarget}
          labelSuggestions={labelOptions}
          onClose={() => setSuggestTarget(null)}
        />
      )}
    </div>
  );
}

function CardEditForm({ form, setForm, decks, allowDeck, labelSuggestions, onSave, onCancel }) {
  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  return (
    <div className="bg-white border border-blue-300 rounded shadow p-4 space-y-2">
      <label className="block text-sm font-semibold">Front</label>
      <input value={form.front} onChange={set('front')} className="w-full border p-2 rounded" />
      <label className="block text-sm font-semibold">Back</label>
      <input value={form.back} onChange={set('back')} className="w-full border p-2 rounded" />
      <label className="block text-sm font-semibold">Labels</label>
      <TagInput
        tags={form.labels}
        onChange={(labels) => setForm((f) => ({ ...f, labels }))}
        suggestions={labelSuggestions}
      />
      {allowDeck && (
        <>
          <label className="block text-sm font-semibold">Deck</label>
          <select value={form.deck_id} onChange={set('deck_id')} className="w-full border p-2 rounded">
            <option value="">— No deck —</option>
            {decks.map((d) => (
              <option key={d.deck_id} value={d.deck_id}>{d.name}</option>
            ))}
          </select>
        </>
      )}
      <div className="flex gap-2 justify-end pt-1">
        <button onClick={onCancel} className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300">Cancel</button>
        <button onClick={onSave} className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">Save</button>
      </div>
    </div>
  );
}
