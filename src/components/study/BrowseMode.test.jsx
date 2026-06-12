import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import BrowseMode from './BrowseMode';
import { AuthProvider } from '../../context/AuthContext';
import { ToastProvider } from '../../context/ToastContext';

const renderBrowse = (props) =>
  render(
    <ToastProvider>
      <AuthProvider>
        <BrowseMode {...props} />
      </AuthProvider>
    </ToastProvider>
  );

beforeEach(() => {
  globalThis.fetch = vi.fn().mockResolvedValue({
    status: 200,
    ok: true,
    text: async () =>
      JSON.stringify({
        cards: [
          { card_id: '1', front: 'a', back: 'A', labels: [] },
          { card_id: '2', front: 'b', back: 'B', labels: [] },
        ],
      }),
  });
});

describe('BrowseMode', () => {
  it('navigates forward and wraps around', async () => {
    renderBrowse({ deckId: '' });

    // First card loaded.
    expect(await screen.findByText('a')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Next ➡️'));
    expect(screen.getByText('b')).toBeInTheDocument();
    expect(screen.queryByText('a')).not.toBeInTheDocument();

    // Wrap back to the first card.
    fireEvent.click(screen.getByText('Next ➡️'));
    expect(screen.getByText('a')).toBeInTheDocument();
  });
});
