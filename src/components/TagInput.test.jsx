import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import TagInput from './TagInput';

describe('TagInput', () => {
  it('adds a tag on Enter and removes it via ×', () => {
    const onChange = vi.fn();
    const { rerender } = render(<TagInput tags={[]} onChange={onChange} />);

    const input = screen.getByRole('combobox');
    fireEvent.change(input, { target: { value: 'verb' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(onChange).toHaveBeenCalledWith(['verb']);

    // Re-render with the tag present, then remove it.
    rerender(<TagInput tags={['verb']} onChange={onChange} />);
    fireEvent.click(screen.getByLabelText('Remove verb'));
    expect(onChange).toHaveBeenLastCalledWith([]);
  });

  it('does not add duplicate tags', () => {
    const onChange = vi.fn();
    render(<TagInput tags={['verb']} onChange={onChange} />);
    const input = screen.getByRole('combobox');
    fireEvent.change(input, { target: { value: 'verb' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(onChange).not.toHaveBeenCalled();
  });
});
