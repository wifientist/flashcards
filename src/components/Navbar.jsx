import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation(); // Optional: for active route highlighting

  return (
    <nav className="fixed top-0 w-full bg-white border-b z-50">
      <div className="max-w-screen-lg mx-auto flex justify-between items-center p-4">
        <div className="text-lg font-bold">Flashcards</div>

        {/* Desktop Nav */}
        <div className="hidden md:flex space-x-4">
        <Link
            to="/create"
            className={`px-3 py-1 border rounded hover:bg-gray-100 transition ${
              location.pathname === '/create' ? 'bg-gray-200' : ''
            }`}
          >
            Create
          </Link>
          <Link
            to="/unlock"
            className={`px-3 py-1 border rounded hover:bg-gray-100 transition ${
              location.pathname === '/unlock' ? 'bg-gray-200' : ''
            }`}
          >
            Unlock
          </Link>
          <Link
            to="/"
            className={`px-3 py-1 border rounded hover:bg-gray-100 transition ${
              location.pathname === '/' ? 'bg-gray-200' : ''
            }`}
          >
            View
          </Link>
          <Link
            to="/study"
            className={`px-3 py-1 border rounded hover:bg-gray-100 transition ${
              location.pathname === '/study' ? 'bg-gray-200' : ''
            }`}
          >
            Study
          </Link>
        </div>

        {/* Hamburger Button */}
        <button
          className="md:hidden focus:outline-none"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d={menuOpen ? 'M6 18L18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h16'}
            />
          </svg>
        </button>
      </div>

      {/* Mobile Menu */}
      {menuOpen && (
        <div className="md:hidden bg-white border-t p-4 space-y-2">
          <Link
            to="/create"
            className="block px-3 py-1 border rounded hover:bg-gray-100 transition"
            onClick={() => setMenuOpen(false)}
          >
            Create
          </Link>
          <Link
            to="/unlock"
            className="block px-3 py-1 border rounded hover:bg-gray-100 transition"
            onClick={() => setMenuOpen(false)}
          >
            Unlock
          </Link>
          <Link
            to="/"
            className="block px-3 py-1 border rounded hover:bg-gray-100 transition"
            onClick={() => setMenuOpen(false)}
          >
            View
          </Link>
          <Link
            to="/study"
            className="block px-3 py-1 border rounded hover:bg-gray-100 transition"
            onClick={() => setMenuOpen(false)}
          >
            Study
          </Link>
        </div>
      )}
    </nav>
  );
}
