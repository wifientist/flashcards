import React from 'react';
import { Link } from 'react-router-dom';

// Shown on Study and Cards when the user has no deck subscriptions. Subscriptions
// are the study universe, so with none there's nothing to show — point the user
// to the Decks page to subscribe.
export default function SubscribePrompt({ what = 'studying' }) {
  return (
    <div className="text-center max-w-md mx-auto mt-12 px-4">
      <p className="text-lg font-semibold mb-1">No subscribed decks yet</p>
      <p className="text-gray-600 text-sm mb-4">
        Subscribe to a deck to start {what}. Your subscribed decks are the pool
        that the queue and filters draw from.
      </p>
      <Link
        to="/manage"
        className="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Browse decks →
      </Link>
    </div>
  );
}
