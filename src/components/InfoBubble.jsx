import React, { useState, useRef, useEffect } from 'react';

// Small "?" button that toggles a popover of explanatory text. Click outside to
// close. Use for inline help (e.g. "where are my cards?").
export default function InfoBubble({ title, children, className = '' }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onDocClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  return (
    <div className={`relative inline-block ${className}`} ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={title || 'Help'}
        className="w-5 h-5 rounded-full border border-gray-400 text-gray-500 text-xs font-semibold leading-none hover:bg-gray-100"
      >
        ?
      </button>
      {open && (
        <div className="absolute z-40 mt-1 left-1/2 -translate-x-1/2 w-72 max-w-[90vw] bg-white border rounded-lg shadow-lg p-3 text-left text-sm text-gray-700 space-y-2">
          {title && <p className="font-semibold">{title}</p>}
          {children}
        </div>
      )}
    </div>
  );
}
