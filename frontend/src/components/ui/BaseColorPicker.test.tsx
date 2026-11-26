import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import BaseColorPicker from './BaseColorPicker';

const OPTIONS = [
  { id: 'white', label: 'Білий', swatch: '#ffffff' },
  { id: 'ocean', label: 'Океан', swatch: '#6387bd' },
  { id: 'sky', label: 'Небо', swatch: '#a9d4ef' },
];

function renderPicker(value: string, isDisabled = false) {
  const onChange = vi.fn();
  render(
    <BaseColorPicker
      options={OPTIONS}
      value={value}
      onChange={onChange}
      label="Колір застосунку"
      isDisabled={isDisabled}
    />,
  );
  return onChange;
}

describe('BaseColorPicker', () => {
  afterEach(cleanup);

  it('is a named radio group with one checked colour', () => {
    renderPicker('ocean');
    expect(screen.getByRole('radiogroup', { name: 'Колір застосунку' })).toBeTruthy();
    expect(screen.getAllByRole('radio')).toHaveLength(3);
    expect(screen.getByRole('radio', { name: 'Океан' }).getAttribute('aria-checked')).toBe('true');
    expect(screen.getByRole('radio', { name: 'Білий' }).getAttribute('aria-checked')).toBe('false');
  });

  it('puts only the checked colour in the tab order', () => {
    renderPicker('sky');
    expect(screen.getByRole('radio', { name: 'Небо' }).tabIndex).toBe(0);
    expect(screen.getByRole('radio', { name: 'Білий' }).tabIndex).toBe(-1);
  });

  it('reports the clicked colour', () => {
    const onChange = renderPicker('white');
    fireEvent.click(screen.getByRole('radio', { name: 'Небо' }));
    expect(onChange).toHaveBeenCalledWith('sky');
  });

  it('moves with the arrow keys and wraps around', () => {
    const onChange = renderPicker('white');
    const group = screen.getByRole('radiogroup');
    fireEvent.keyDown(group, { key: 'ArrowRight' });
    expect(onChange).toHaveBeenLastCalledWith('ocean');
    fireEvent.keyDown(group, { key: 'ArrowLeft' });
    expect(onChange).toHaveBeenLastCalledWith('sky');
  });

  it('jumps to the first and last colour with Home and End', () => {
    const onChange = renderPicker('ocean');
    const group = screen.getByRole('radiogroup');
    fireEvent.keyDown(group, { key: 'End' });
    expect(onChange).toHaveBeenLastCalledWith('sky');
    fireEvent.keyDown(group, { key: 'Home' });
    expect(onChange).toHaveBeenLastCalledWith('white');
  });

  it('ignores clicks and keys while disabled', () => {
    const onChange = renderPicker('white', true);
    fireEvent.click(screen.getByRole('radio', { name: 'Небо' }));
    fireEvent.keyDown(screen.getByRole('radiogroup'), { key: 'ArrowRight' });
    expect(onChange).not.toHaveBeenCalled();
  });
});
