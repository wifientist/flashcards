import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LogoutButton from './LogoutButton';

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const { user } = useAuth();

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

  // Full-width tap targets for the mobile drawer (vs. the inline pills above).
  const MobileLink = ({ to, children }) => (
    <Link
      to={to}
      className={`block px-4 py-3 rounded-lg text-base transition ${
        location.pathname === to ? 'bg-blue-50 text-blue-700 font-semibold' : 'hover:bg-gray-100'
      }`}
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
        <div className="hidden md:flex space-x-3 items-center">
          {!user && <NavLink to="/">Home</NavLink>}
          {user && <NavLink to="/study">Study</NavLink>}
          <NavLink to="/manage">Manage</NavLink>
          {user && <NavLink to="/profile">Profile</NavLink>}
          {user?.roles?.includes('admin') && <NavLink to="/admin">Admin</NavLink>}
          {!user && <NavLink to="/login">Login</NavLink>}
          {user && (
            <>
              <span className="h-5 w-px bg-gray-300" aria-hidden="true" />
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
        <div className="md:hidden bg-white border-t shadow-lg flex flex-col p-2">
          {!user && <MobileLink to="/">Home</MobileLink>}
          {user && <MobileLink to="/study">Study</MobileLink>}
          <MobileLink to="/manage">Manage</MobileLink>
          {user && <MobileLink to="/profile">Profile</MobileLink>}
          {user?.roles?.includes('admin') && <MobileLink to="/admin">Admin</MobileLink>}
          {!user && <MobileLink to="/login">Login</MobileLink>}
          {user && (
            <>
              <hr className="my-2 border-gray-200" />
              <div className="flex items-center justify-between px-4 py-2">
                <span className="text-sm text-gray-600 truncate">{user.email}</span>
                <LogoutButton />
              </div>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
