import React, { useState } from 'react';

export default function CardAdder() {
  const [front, setFront] = useState('');
  const [back, setBack] = useState('');
  const [labels, setLabels] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();

    const labelArray = labels.split(',').map(label => label.trim()).filter(label => label);

    try {
      const response = await fetch('/api/cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ front, back, labels: labelArray }),
        credentials: 'include',
      });

      if (response.ok) {
        alert('Card created!');
        setFront('');
        setBack('');
        setLabels('');
      } else {
        const error = await response.json();
        alert('Error: ' + JSON.stringify(error.detail));
      }
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="max-w-md mx-auto mt-8 p-6 bg-white rounded-lg shadow-lg space-y-4"
    >
      <h2 className="text-2xl font-bold text-center mb-4">Create a New Flashcard</h2>

      <div>
        <label className="block text-gray-700 mb-1">Front:</label>
        <input
          type="text"
          value={front}
          onChange={(e) => setFront(e.target.value)}
          required
          className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-gray-700 mb-1">Back:</label>
        <input
          type="text"
          value={back}
          onChange={(e) => setBack(e.target.value)}
          required
          className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-gray-700 mb-1">Labels (comma-separated):</label>
        <input
          type="text"
          value={labels}
          onChange={(e) => setLabels(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <button
        type="submit"
        className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 transition-colors"
      >
        Create Card
      </button>
    </form>
  );
}
