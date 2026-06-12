// Shared client-side card filtering, used by the Cards page and Study modes so
// the deck/label/status scope behaves identically everywhere. Deck scope is
// applied server-side (via the query); these handle labels + statuses.

// STATUS_OPTIONS drives the status multi-select. 'starred' and 'due' are derived
// from progress rather than the FSRS status string.
export const STATUS_OPTIONS = [
  { value: 'new', label: 'New' },
  { value: 'learning', label: 'Learning' },
  { value: 'relearning', label: 'Relearning' },
  { value: 'review', label: 'Review' },
  { value: 'mastered', label: 'Mastered' },
  { value: 'difficult', label: 'Difficult' },
  { value: 'due', label: '⏰ Due now' },
  { value: 'starred', label: '★ Starred' },
];

function matchesStatus(card, status, now) {
  const p = card.user_progress || {};
  if (status === 'starred') return !!p.flagged;
  if (status === 'due') return !!p.due && new Date(p.due).getTime() <= now;
  return (p.status || 'new') === status;
}

// A card passes the label filter if it carries at least one selected label
// (case-insensitive). Empty selection = no filter.
function matchesLabels(card, labels) {
  if (!labels.length) return true;
  const have = new Set((card.labels || []).map((l) => l.toLowerCase()));
  return labels.some((l) => have.has(l.toLowerCase()));
}

// Statuses are OR within themselves; labels OR within themselves; the two
// dimensions are ANDed together. Empty dimensions don't filter.
export function cardMatchesFilters(card, { statuses = [], labels = [] }, now = Date.now()) {
  const statusOk = statuses.length === 0 || statuses.some((s) => matchesStatus(card, s, now));
  return statusOk && matchesLabels(card, labels);
}

export function filterCards(cards, filters, now = Date.now()) {
  return cards.filter((c) => cardMatchesFilters(c, filters, now));
}
