import React, { useState, useRef, useEffect } from 'react';

// Generic checkbox multi-select dropdown. `options` is [{ value, label }].
// Empty selection means "all" (no filter).
export default function MultiSelect({ label, options, selected, onChange, allLabel = 'All' }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onDocClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  const toggle = (v) =>
    onChange(selected.includes(v) ? selected.filter((x) => x !== v) : [...selected, v]);

  const summary = selected.length === 0 ? allLabel : `${selected.length}`;

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="border border-gray-300 rounded p-2 text-sm bg-white hover:bg-gray-50"
      >
        {label}: {summary} ▾
      </button>
      {open && (
        <div className="absolute right-0 mt-1 bg-white border rounded shadow-lg p-2 z-30 w-52 max-h-64 overflow-auto text-sm">
          <label className="flex items-center gap-2 py-0.5 cursor-pointer">
            <input type="checkbox" checked={selected.length === 0} onChange={() => onChange([])} />
            <span className="font-medium">{allLabel}</span>
          </label>
          {options.length > 0 && <hr className="my-1" />}
          {options.map((o) => (
            <label key={o.value} className="flex items-center gap-2 py-0.5 cursor-pointer">
              <input
                type="checkbox"
                checked={selected.includes(o.value)}
                onChange={() => toggle(o.value)}
              />
              <span className="truncate">{o.label}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
