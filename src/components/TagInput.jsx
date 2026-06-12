import React, { useId, useState } from 'react';

// Chip-based tag editor with autocomplete from `suggestions`.
// `tags` is an array of strings; `onChange` receives the new array.
export default function TagInput({ tags, onChange, suggestions = [], placeholder = 'Add a label…' }) {
  const [input, setInput] = useState('');
  const listId = useId();

  const addTag = (raw) => {
    const tag = raw.trim();
    if (tag && !tags.includes(tag)) onChange([...tags, tag]);
    setInput('');
  };

  const removeTag = (tag) => onChange(tags.filter((t) => t !== tag));

  const onKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(input);
    } else if (e.key === 'Backspace' && !input && tags.length) {
      removeTag(tags[tags.length - 1]);
    }
  };

  // Don't suggest tags already chosen.
  const available = suggestions.filter((s) => !tags.includes(s));

  return (
    <div className="border border-gray-300 rounded p-1 flex flex-wrap gap-1 items-center">
      {tags.map((tag) => (
        <span key={tag} className="bg-gray-200 rounded px-2 py-0.5 text-sm flex items-center gap-1">
          {tag}
          <button
            type="button"
            onClick={() => removeTag(tag)}
            className="text-gray-500 hover:text-red-600 leading-none"
            aria-label={`Remove ${tag}`}
          >
            ×
          </button>
        </span>
      ))}
      <input
        list={listId}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={onKeyDown}
        onBlur={() => addTag(input)}
        placeholder={tags.length ? '' : placeholder}
        className="flex-1 min-w-[8rem] p-1 outline-none text-sm bg-transparent"
      />
      <datalist id={listId}>
        {available.map((s) => <option key={s} value={s} />)}
      </datalist>
    </div>
  );
}
