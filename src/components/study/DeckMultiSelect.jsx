import React, { useState, useRef, useEffect } from 'react';

// Compact multi-deck picker. Empty selection = "All decks". Persisted by the
// parent (server-side).
export default function DeckMultiSelect({ decks, selected, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onDocClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  const toggle = (id) =>
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);

  const label = selected.length === 0
    ? 'All decks'
    : `${selected.length} deck${selected.length > 1 ? 's' : ''}`;

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="border rounded p-1 px-2 text-sm bg-white hover:bg-gray-50"
      >
        Decks: {label} ▾
      </button>
      {open && (
        <div className="absolute right-0 mt-1 bg-white border rounded shadow-lg p-2 z-30 w-52 max-h-64 overflow-auto text-sm">
          <label className="flex items-center gap-2 py-0.5 cursor-pointer">
            <input type="checkbox" checked={selected.length === 0} onChange={() => onChange([])} />
            <span className="font-medium">All decks</span>
          </label>
          {decks.length > 0 && <hr className="my-1" />}
          {decks.map((d) => (
            <label key={d.deck_id} className="flex items-center gap-2 py-0.5 cursor-pointer">
              <input
                type="checkbox"
                checked={selected.includes(d.deck_id)}
                onChange={() => toggle(d.deck_id)}
              />
              <span className="truncate">{d.name}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
