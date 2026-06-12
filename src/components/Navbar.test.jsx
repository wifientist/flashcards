import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Navbar from './Navbar';
import { AuthProvider } from '../context/AuthContext';

function renderNavbar() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <Navbar />
      </AuthProvider>
    </MemoryRouter>
  );
}

beforeEach(() => {
  // AuthProvider calls whoami on mount.
  globalThis.fetch = vi.fn().mockResolvedValue({
    status: 200,
    ok: true,
    text: async () => JSON.stringify({ authenticated: false, roles: ['guest'] }),
  });
});

describe('Navbar', () => {
  it('shows brand, public links, and Login when logged out', async () => {
    renderNavbar();
    expect(await screen.findByText('Flashcards')).toBeInTheDocument();
    expect(screen.getByText('Decks')).toBeInTheDocument();
    // Login shown to guests; authed-only links hidden
    expect(screen.getAllByText('Login').length).toBeGreaterThan(0);
    expect(screen.queryByText('Study')).not.toBeInTheDocument();
    expect(screen.queryByText('Admin')).not.toBeInTheDocument();
  });
});
