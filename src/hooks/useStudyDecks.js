import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

// Loads the visible decks and the user's persisted study deck scope, and saves
// changes back to the server. `enabled` gates the (authenticated) scope fetch.
export function useStudyDecks(enabled = true) {
  const [decks, setDecks] = useState([]);
  const [selectedDeckIds, setSelectedDeckIds] = useState([]);

  useEffect(() => {
    api.get('/api/decks').then((d) => setDecks(d.decks || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (!enabled) return;
    api.get('/api/auth/me/study-decks').then((d) => setSelectedDeckIds(d.deck_ids || [])).catch(() => {});
  }, [enabled]);

  const updateDecks = useCallback((ids) => {
    setSelectedDeckIds(ids);
    api.put('/api/auth/me/study-decks', { deck_ids: ids }).catch(() => {});
  }, []);

  return { decks, selectedDeckIds, updateDecks };
}
