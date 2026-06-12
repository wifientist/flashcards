import React from 'react';
import MultiSelect from '../MultiSelect';

// Deck-scoped wrapper around the generic MultiSelect.
export default function DeckMultiSelect({ decks, selected, onChange }) {
  const options = decks.map((d) => ({ value: d.deck_id, label: d.name }));
  return (
    <MultiSelect label="Decks" options={options} selected={selected} onChange={onChange} allLabel="All decks" />
  );
}
