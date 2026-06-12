import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LogoutButton from './LogoutButton';

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const { user } = useAuth();

  // Only trusted users (and admins) may create cards.
  const canCreate = user?.roles?.some((r) => r === 'admin' || r === 'trusted');

  const isActive = (path) => location.pathname === path ? 'bg-gray-200' : '';

  const NavLink = ({ to, children }) => (
    <Link
      to={to}
      className={`px-3 py-1 border rounded hover:bg-gray-100 transition ${isActive(to)}`}
      onClick={() => setMenuOpen(false)}
    >
      {children}
    </Link>
  );

  return (
    <nav className="fixed top-0 w-full bg-white border-b z-50">
      <div className="max-w-screen-lg mx-auto flex justify-between items-center p-4">
        <Link to="/" className="text-lg font-bold" onClick={() => setMenuOpen(false)}>Flashcards</Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex space-x-4 items-center">
          <NavLink to="/">Home</NavLink>
          <NavLink to="/view">View</NavLink>
          <NavLink to="/decks">Decks</NavLink>
          {canCreate && <NavLink to="/create">Create</NavLink>}
          {user && <NavLink to="/study">Study</NavLink>}
          {user && <NavLink to="/dashboard">Dashboard</NavLink>}
          {user?.roles?.includes('admin') && <NavLink to="/admin">Admin</NavLink>}
          {!user && <NavLink to="/login">Login</NavLink>}
          {user && (
            <>
              <span className="text-sm text-gray-600">Hi, {user.email}</span>
              <LogoutButton />
            </>
          )}
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
          <NavLink to="/">Home</NavLink>
          <NavLink to="/view">View</NavLink>
          <NavLink to="/decks">Decks</NavLink>
          {canCreate && <NavLink to="/create">Create</NavLink>}
          {user && <NavLink to="/study">Study</NavLink>}
          {user && <NavLink to="/dashboard">Dashboard</NavLink>}
          {user?.roles?.includes('admin') && <NavLink to="/admin">Admin</NavLink>}
          {!user && <NavLink to="/login">Login</NavLink>}
          {user && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">{user.email}</span>
              <LogoutButton />
            </div>
          )}
        </div>
      )}
    </nav>
  );
}
