import React, { useState, useEffect } from 'react';
import { useSwipeable } from 'react-swipeable';

export default function CardStudy() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [swipeDirection, setSwipeDirection] = useState('');
  const [editNote, setEditNote] = useState('');
  const [editStatus, setEditStatus] = useState('');
  const [showEdit, setShowEdit] = useState(false);


  useEffect(() => {
    const fetchCards = async () => {
      try {
        const response = await fetch('/api/cards', { credentials: 'include' });
        if (!response.ok) throw new Error('Failed to fetch cards');
        const data = await response.json();
        setCards(data.cards);
        console.log(data.cards);
      } catch (err) {
        console.error(err);
        alert('Error fetching cards');
      } finally {
        setLoading(false);
      }
    };

    fetchCards();
  }, []);

  useEffect(() => {
    if (!cards.length) return;
    const progress = cards[currentIndex]?.user_progress || {};
    setEditNote(progress.notes || '');
    setEditStatus(progress.status || 'new');
    setShowEdit(false);
  }, [currentIndex, cards]);

  const handleNext = () => {
    if (cards.length === 0 || isAnimating) return;
    
    setIsAnimating(true);
    setSwipeDirection('left');
    
    setTimeout(() => {
      if (flipped) setFlipped(false);
      setCurrentIndex((prev) => (prev + 1) % cards.length);
      setSwipeDirection('');
      setIsAnimating(false);
    }, 400);
  };

  const handlePrev = () => {
    if (cards.length === 0 || isAnimating) return;
    
    setIsAnimating(true);
    setSwipeDirection('right');
    
    setTimeout(() => {
      if (flipped) setFlipped(false);
      setCurrentIndex((prev) => (prev - 1 + cards.length) % cards.length);
      setSwipeDirection('');
      setIsAnimating(false);
    }, 400);
  };

  const handlers = useSwipeable({
    onSwipedLeft: () => handlePrev(),
    onSwipedRight: () => handleNext(),
    trackMouse: true,
  });

  if (loading) return <p className="text-center mt-8">Loading cards...</p>;

  if (cards.length === 0) return <p className="text-center mt-8">No cards available.</p>;

  const currentCard = cards[currentIndex];
  const progress = currentCard.user_progress || {};
  const status = progress.status || "new";
  const reviewCount = progress.review_count || 0;
  const lastReviewed = progress.last_reviewed
    ? new Date(progress.last_reviewed).toLocaleDateString()
    : "Never";
  const note = progress.notes || "";

  return (
    <div {...handlers} className="flex flex-col" style={{ height: 'calc(100vh - 5rem)' }}>
      {/* Flip Card Container - 80% of available height */}
      <div className="h-5/6 perspective px-4 pt-4 flex items-center justify-center overflow-hidden">
        <div
          onClick={() => !isAnimating && setFlipped(!flipped)}
          className={`relative w-full h-full max-w-2xl mx-auto transition-all duration-500 transform cursor-pointer
            ${flipped && !isAnimating ? 'rotate-y-180' : ''}
            ${swipeDirection === 'left' ? 'translate-x-full rotate-12 opacity-0' : ''}
            ${swipeDirection === 'right' ? '-translate-x-full -rotate-12 opacity-0' : ''}
            ${isAnimating ? 'ease-out' : 'ease-in-out'}
          `}
          style={{ 
            transformStyle: 'preserve-3d'
          }}
        >
          {/* Front Face */}
          <div className="absolute w-full h-full bg-white border rounded-lg shadow-lg flex items-center justify-center text-2xl text-center p-6" 
               style={{ backfaceVisibility: 'hidden' }}>
            <div>{currentCard.front}</div>
            <div className="absolute top-2 left-2 bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-1 rounded shadow">
              {status.toUpperCase()} • {reviewCount} 🔁 • {lastReviewed}
            </div>
          </div>
  
          {/* Back Face */}
          <div className="absolute w-full h-full bg-white border rounded-lg shadow-lg flex items-center justify-center text-2xl text-center p-6 transform rotate-y-180" 
               style={{ backfaceVisibility: 'hidden' }}>
            <div>
              <div>{currentCard.back}</div>
              {note && (
                <div className="mt-4 text-sm text-gray-500 border-t pt-2">
                  <strong>Note:</strong> {note}
                </div>
              )}
              {showEdit ? (
                <div className="mt-4 text-left w-full text-sm">
                  <label className="block mb-1 font-semibold">Status</label>
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value)}
                    className="w-full border rounded p-1 mb-2"
                  >
                    <option value="new">New</option>
                    <option value="learning">Learning</option>
                    <option value="review">Review</option>
                    <option value="mastered">Mastered</option>
                    <option value="difficult">Difficult</option>
                  </select>

                  <label className="block mb-1 font-semibold">Note</label>
                  <textarea
                    value={editNote}
                    onChange={(e) => setEditNote(e.target.value)}
                    rows={3}
                    className="w-full border rounded p-1"
                  />

                  <div className="flex justify-end mt-2 space-x-2">
                    <button
                      className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
                      onClick={() => setShowEdit(false)}
                    >
                      Cancel
                    </button>
                    <button
                      className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                      onClick={async () => {
                        const cardId = cards[currentIndex].card_id;
                        try {
                          const res = await fetch(`/api/cards/${cardId}/progress`, {
                            method: 'PUT',
                            credentials: 'include',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              notes: editNote,
                              status: editStatus,
                            }),
                          });
                          if (!res.ok) throw new Error('Failed to update progress');
                          alert('Progress saved!');
                          setShowEdit(false);
                        } catch (err) {
                          console.error(err);
                          alert('Error saving progress');
                        }
                      }}
                    >
                      Save
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowEdit(true)}
                  className="absolute bottom-4 right-4 text-xs text-blue-600 underline"
                >
                  ✏️ Edit Progress
                </button>
              )}

            </div>
          </div>
        </div>
      </div>
  
      {/* Navigation Arrows - 20% of screen height */}
      <div className="h-1/6 flex items-center justify-center px-4">
        <div className="flex justify-between w-full max-w-xs space-x-8">
          <button
            onClick={handlePrev}
            className="px-4 py-2 border rounded hover:bg-gray-100 transition bg-white"
          >
            ⬅️ Prev
          </button>
          <button
            onClick={handleNext}
            className="px-4 py-2 border rounded hover:bg-gray-100 transition bg-white"
          >
            Next ➡️
          </button>
        </div>
      </div>
    </div>
  );

}
