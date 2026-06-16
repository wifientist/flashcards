import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

// Loads the visible decks + the label vocabulary, plus the user's persisted
// label/status filter scope (shared across the Cards and Study pages, saved
// server-side per profile).
//
// Deck scope is no longer a transient filter: it's the user's *subscriptions*.
// Subscriptions are the study universe — the queue and card list scope to the
// decks the user has subscribed to (derived here as `subscribedDeckIds` from the
// decks list's per-deck `subscribed` flag). `enabled` gates the authenticated
// fetch/save (guests filter in-session only).
export function useStudyFilters(enabled = true) {
  const [decks, setDecks] = useState([]);
  const [labelOptions, setLabelOptions] = useState([]);
  const [sel, setSel] = useState({ labels: [], statuses: [] });

  const reloadDecks = useCallback(() => {
    api.get('/api/decks').then((d) => setDecks(d.decks || [])).catch(() => {});
  }, []);

  const reloadLabels = useCallback(() => {
    api.get('/api/labels').then((d) => setLabelOptions((d.labels || []).map((l) => l.label))).catch(() => {});
  }, []);

  useEffect(() => { reloadDecks(); reloadLabels(); }, [reloadDecks, reloadLabels]);

  useEffect(() => {
    if (!enabled) return;
    api.get('/api/auth/me/study-filters')
      .then((d) => setSel({ labels: d.labels || [], statuses: d.statuses || [] }))
      .catch(() => {});
  }, [enabled]);

  // Merge a partial change into the scope and persist the whole set. Deck scope
  // lives in subscriptions now, so only labels/statuses are sent (deck_ids kept
  // empty for back-compat with the persisted-filters endpoint).
  const update = useCallback((partial) => {
    setSel((prev) => {
      const next = { ...prev, ...partial };
      if (enabled) api.put('/api/auth/me/study-filters', { ...next, deck_ids: [] }).catch(() => {});
      return next;
    });
  }, [enabled]);

  // Subscribe / unsubscribe toggles, then refresh decks so `subscribed` (and
  // thus subscribedDeckIds) reflects the change.
  const subscribe = useCallback(async (deckId) => {
    await api.post(`/api/decks/${deckId}/subscribe`);
    reloadDecks();
  }, [reloadDecks]);

  const unsubscribe = useCallback(async (deckId) => {
    await api.del(`/api/decks/${deckId}/subscribe`);
    reloadDecks();
  }, [reloadDecks]);

  return {
    decks,
    reloadDecks,
    labelOptions,
    reloadLabels,
    subscribedDeckIds: decks.filter((d) => d.subscribed).map((d) => d.deck_id),
    subscribe,
    unsubscribe,
    selectedLabels: sel.labels,
    selectedStatuses: sel.statuses,
    updateLabels: useCallback((labels) => update({ labels }), [update]),
    updateStatuses: useCallback((statuses) => update({ statuses }), [update]),
  };
}
