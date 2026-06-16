import React from 'react';

// The shared "how studying works / where are my cards?" explanation, reused in
// the Study and Dashboard info bubbles.
export default function StudyExplainer() {
  return (
    <div className="space-y-2">
      <p><strong>Subscriptions</strong> — your study pool is the decks you’ve <em>subscribed</em> to (on the Decks page). Everything below draws only from those decks; label and status filters then narrow within them.</p>
      <p><strong>New</strong> — never-seen cards. Up to 20 join each batch so you’re not flooded; finish them and tap <em>Introduce more</em> for the next 20.</p>
      <p><strong>Due</strong> — cards you’ve learned that are scheduled for review now. All of them show, most-overdue first.</p>
      <p><strong>Resting</strong> — cards you reviewed recently are hidden until their next due date. That’s spaced repetition (FSRS): reviewing too early wastes effort, and intervals stretch out as your memory strengthens.</p>
      <p className="text-gray-500">Don’t see a card? Its deck may not be subscribed, it’s resting until its due date, or it’s filtered out by your label / status selection.</p>
    </div>
  );
}
