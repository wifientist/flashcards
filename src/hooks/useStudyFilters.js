import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

// Loads the visible decks + the label vocabulary, plus the user's persisted
// filter scope (decks + labels + statuses) which is shared across the Cards and
// Study pages and saved server-side per profile. `enabled` gates the
// authenticated fetch/save (guests filter in-session only).
export function useStudyFilters(enabled = true) {
  const [decks, setDecks] = useState([]);
  const [labelOptions, setLabelOptions] = useState([]);
  const [sel, setSel] = useState({ deck_ids: [], labels: [], statuses: [] });

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
      .then((d) => setSel({
        deck_ids: d.deck_ids || [],
        labels: d.labels || [],
        statuses: d.statuses || [],
      }))
      .catch(() => {});
  }, [enabled]);

  // Merge a partial change into the scope and persist the whole set.
  const update = useCallback((partial) => {
    setSel((prev) => {
      const next = { ...prev, ...partial };
      if (enabled) api.put('/api/auth/me/study-filters', next).catch(() => {});
      return next;
    });
  }, [enabled]);

  return {
    decks,
    reloadDecks,
    labelOptions,
    reloadLabels,
    selectedDeckIds: sel.deck_ids,
    selectedLabels: sel.labels,
    selectedStatuses: sel.statuses,
    updateDecks: useCallback((deck_ids) => update({ deck_ids }), [update]),
    updateLabels: useCallback((labels) => update({ labels }), [update]),
    updateStatuses: useCallback((statuses) => update({ statuses }), [update]),
  };
}
