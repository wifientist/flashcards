import React, { useState, useEffect } from 'react';
import { useSwipeable } from 'react-swipeable';

export default function CardStudy() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [swipeDirection, setSwipeDirection] = useState('');

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
            {currentCard.front}
          </div>
  
          {/* Back Face */}
          <div className="absolute w-full h-full bg-white border rounded-lg shadow-lg flex items-center justify-center text-2xl text-center p-6 transform rotate-y-180" 
               style={{ backfaceVisibility: 'hidden' }}>
            {currentCard.back}
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
