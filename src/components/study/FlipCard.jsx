import React from 'react';

// Shared flip-card visual used by both study modes. Relies on the 3D utility
// classes defined in src/index.css (perspective / rotate-y-180 / preserve-3d).
export default function FlipCard({ front, back, flipped, onClick, badge }) {
  return (
    <div className="flex-1 perspective px-4 pt-2 flex items-center justify-center overflow-hidden">
      <div
        onClick={onClick}
        className={`relative w-full h-full max-w-2xl mx-auto transition-transform duration-500 cursor-pointer
          ${flipped ? 'rotate-y-180' : ''}`}
        style={{ transformStyle: 'preserve-3d' }}
      >
        {/* Front */}
        <div
          className="absolute w-full h-full bg-white border rounded-lg shadow-lg flex items-center justify-center text-2xl text-center p-6"
          style={{ backfaceVisibility: 'hidden' }}
        >
          <div>{front}</div>
          {badge && (
            <div className="absolute top-2 left-2 text-xs text-gray-400">{badge}</div>
          )}
        </div>

        {/* Back */}
        <div
          className="absolute w-full h-full bg-white border rounded-lg shadow-lg flex items-center justify-center text-2xl text-center p-6 rotate-y-180"
          style={{ backfaceVisibility: 'hidden' }}
        >
          <div>{back}</div>
        </div>
      </div>
    </div>
  );
}
