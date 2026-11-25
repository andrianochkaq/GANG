import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, it } from 'vitest';

import '../../i18n';
import BaseCodeInput from './BaseCodeInput';

function CodeInputHarness() {
  const [code, setCode] = useState('');
  return (
    <>
      <BaseCodeInput value={code} onChange={setCode} legend="Code" />
      <output data-testid="code">{code}</output>
    </>
  );
}

function getCell(index: number): HTMLInputElement {
  return screen.getByLabelText(`Цифра ${index}`);
}

describe('BaseCodeInput', () => {
  afterEach(cleanup);

  it('moves to the next cell after each digit', () => {
    render(<CodeInputHarness />);
    fireEvent.change(getCell(1), { target: { value: '4' } });
    expect(document.activeElement).toBe(getCell(2));
    fireEvent.change(getCell(2), { target: { value: '8' } });
    expect(screen.getByTestId('code').textContent).toBe('48');
  });

  it('fills every cell from a pasted code and ignores other characters', () => {
    render(<CodeInputHarness />);
    fireEvent.paste(getCell(1), { clipboardData: { getData: () => '12 34-56' } });
    expect(screen.getByTestId('code').textContent).toBe('123456');
    expect(getCell(6).value).toBe('6');
  });

  it('goes back and clears with Backspace', () => {
    render(<CodeInputHarness />);
    fireEvent.paste(getCell(1), { clipboardData: { getData: () => '123' } });
    fireEvent.keyDown(getCell(4), { key: 'Backspace' });
    expect(screen.getByTestId('code').textContent).toBe('12');
    expect(document.activeElement).toBe(getCell(3));
  });
});
